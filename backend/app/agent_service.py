import asyncio
import json
import logging
import time
from collections.abc import Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any

from agents import Agent, Runner, set_default_openai_key
from agents.mcp import (
    MCPServerStreamableHttp,
    create_static_tool_filter,
)

from app.settings import Settings
from app.store import GameRecord, GameStore, PlayerType

APPROVED_AGENT_TOOLS = (
    "create_game",
    "get_game_state",
    "make_move",
    "reset_game",
)

agent_logger = logging.getLogger("tic_tac_toe.agent")


@dataclass
class _GameLockEntry:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    references: int = 0


class AgentTurnUnavailableError(ValueError):
    """Raised when the requested game is not ready for an AI agent turn."""


class AgentConfigurationError(RuntimeError):
    """Raised when the runtime agent is not safely configured."""


class AgentTurnError(RuntimeError):
    """Raised when an agent run does not produce one accepted move."""


class AgentTurnService:
    def __init__(
        self,
        *,
        settings: Settings,
        store: GameStore,
        server_factory: Callable[..., Any] = MCPServerStreamableHttp,
        agent_factory: Callable[..., Any] = Agent,
        runner: Any = Runner,
    ) -> None:
        self.settings = settings
        self.store = store
        self.server_factory = server_factory
        self.agent_factory = agent_factory
        self.runner = runner
        self._agent: Any | None = None
        self._server_stack: AsyncExitStack | None = None
        self._lifecycle_lock = asyncio.Lock()
        self._game_locks: dict[str, _GameLockEntry] = {}
        self._active_agent_runs = 0
        self._agent_is_stale = False
        self._no_active_agent_runs = asyncio.Event()
        self._no_active_agent_runs.set()

    async def run(self, game_id: str) -> GameRecord:
        lock_entry = self._game_locks.get(game_id)
        if lock_entry is None:
            lock_entry = _GameLockEntry()
            self._game_locks[game_id] = lock_entry
        lock_entry.references += 1
        try:
            async with lock_entry.lock:
                return await self._run_locked(game_id)
        finally:
            lock_entry.references -= 1
            if (
                lock_entry.references == 0
                and self._game_locks.get(game_id) is lock_entry
            ):
                del self._game_locks[game_id]

    async def _run_locked(self, game_id: str) -> GameRecord:
        before = self.store.get(game_id)
        self._validate_turn(before)
        current_player = before.game.current_player
        if current_player is None:
            raise AgentTurnUnavailableError("agent turn is not currently available")
        before_turn = before.game.turn
        if (
            self.settings.openai_api_key is None
            or not self.settings.openai_api_key.get_secret_value().strip()
        ):
            raise AgentConfigurationError("OpenAI API key is not configured")
        if self.settings.light_speed_mcp_transport != "streamable_http":
            raise AgentConfigurationError("unsupported MCP transport")

        started_at = time.perf_counter()
        setup_started_at = started_at
        runner_started_at = started_at
        setup_ms = 0.0
        runner_ms = 0.0
        mcp_session_reused = False
        success = False
        error_type: str | None = None
        try:
            setup_started_at = time.perf_counter()
            agent, mcp_session_reused = await self._ensure_agent()
            setup_ms = (time.perf_counter() - setup_started_at) * 1000
            runner_started_at = time.perf_counter()
            self._active_agent_runs += 1
            self._no_active_agent_runs.clear()
            try:
                await self.runner.run(agent, f"Make one move for game_id={game_id}.")
            except Exception:
                await self._invalidate_agent()
                raise
            finally:
                self._active_agent_runs -= 1
                if self._active_agent_runs == 0:
                    self._no_active_agent_runs.set()
                    if self._agent_is_stale:
                        await self._close_cached_agent()
            runner_ms = (time.perf_counter() - runner_started_at) * 1000

            after = self.store.get(game_id)
            if after.game.turn != before_turn + 1:
                raise AgentTurnError("agent did not make exactly one legal move")
            success = True
            return after
        except Exception as exc:
            error_type = type(exc).__name__
            if isinstance(exc, AgentTurnError):
                raise
            raise AgentTurnError("agent runtime failed") from exc
        finally:
            event = {
                "agent_setup_ms": round(setup_ms, 2),
                "event": "agent_turn_latency",
                "game_id": game_id,
                "mcp_session_reused": mcp_session_reused,
                "runner_ms": round(runner_ms, 2),
                "success": success,
                "total_ms": round((time.perf_counter() - started_at) * 1000, 2),
            }
            if error_type is not None:
                event["error_type"] = error_type
            agent_logger.info(json.dumps(event, sort_keys=True))

    async def _ensure_agent(self) -> tuple[Any, bool]:
        while True:
            async with self._lifecycle_lock:
                if self._agent is not None and not self._agent_is_stale:
                    return self._agent, True
                if self._agent_is_stale:
                    wait_for_idle = self._no_active_agent_runs
                else:
                    return await self._create_agent()
            await wait_for_idle.wait()

    async def _create_agent(self) -> tuple[Any, bool]:
        set_default_openai_key(self.settings.openai_api_key.get_secret_value())
        mcp_url = f"{str(self.settings.light_speed_mcp_url).rstrip('/')}/"
        stack = AsyncExitStack()
        try:
            server = self.server_factory(
                name="Tic-Tac-Toe Light Speed MCP",
                params={
                    "url": mcp_url,
                    "timeout": self.settings.light_speed_mcp_timeout_seconds,
                },
                cache_tools_list=True,
                tool_filter=create_static_tool_filter(
                    allowed_tool_names=list(APPROVED_AGENT_TOOLS)
                ),
                failure_error_function=None,
            )
            connected_server = await stack.enter_async_context(server)
            agent = self.agent_factory(
                name="Tic-Tac-Toe AI Player",
                model=self.settings.openai_model,
                instructions=(
                    "You are the game-playing AI. Use only the provided game MCP tools. "
                    "For each request, play exactly one legal move for the requested game. "
                    "First inspect the state with get_game_state. Then call make_move "
                    "with the requested index and actor='ai-agent'. Do not create a "
                    "different game, reset the game, or use tools outside the requested game."
                ),
                mcp_servers=[connected_server],
                mcp_config={
                    "convert_schemas_to_strict": True,
                    "failure_error_function": None,
                },
            )
        except Exception:
            await stack.aclose()
            raise

        self._server_stack = stack
        self._agent = agent
        return agent, False

    async def _invalidate_agent(self) -> None:
        async with self._lifecycle_lock:
            self._agent_is_stale = True
            if self._active_agent_runs == 0:
                await self._close_cached_agent_locked()

    async def _close_cached_agent(self) -> None:
        async with self._lifecycle_lock:
            await self._close_cached_agent_locked()

    async def _close_cached_agent_locked(self) -> None:
        stack = self._server_stack
        self._server_stack = None
        self._agent = None
        self._agent_is_stale = False
        if stack is not None:
            await stack.aclose()

    async def close(self) -> None:
        await self._close_cached_agent()

    @staticmethod
    def _validate_turn(record: GameRecord) -> None:
        current_player = record.game.current_player
        if current_player is None or record.players.for_player(current_player) is not PlayerType.AI_AGENT:
            raise AgentTurnUnavailableError("agent turn is not currently available")
