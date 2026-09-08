from collections.abc import Callable
from typing import Any

from agents import Agent, Runner, set_default_openai_key
from agents.mcp import (
    MCPServerStreamableHttp,
    create_static_tool_filter,
)

from app.settings import Settings
from app.store import GameMode, GameRecord, GameStore, PlayerType

APPROVED_AGENT_TOOLS = (
    "create_game",
    "get_game_state",
    "make_move",
    "reset_game",
)


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

    async def run(self, game_id: str) -> GameRecord:
        before = self.store.get(game_id)
        self._validate_turn(before)
        current_player = before.game.current_player
        if current_player is None:
            raise AgentTurnUnavailableError("agent turn is not currently available")
        before_turn = before.game.turn
        if self.settings.openai_api_key is None:
            raise AgentConfigurationError("OpenAI API key is not configured")
        if self.settings.light_speed_mcp_transport != "streamable_http":
            raise AgentConfigurationError("unsupported MCP transport")

        try:
            set_default_openai_key(self.settings.openai_api_key.get_secret_value())
            server = self.server_factory(
                name="Tic-Tac-Toe Light Speed MCP",
                params={
                    "url": str(self.settings.light_speed_mcp_url),
                    "timeout": self.settings.light_speed_mcp_timeout_seconds,
                },
                cache_tools_list=True,
                tool_filter=create_static_tool_filter(
                    allowed_tool_names=list(APPROVED_AGENT_TOOLS)
                ),
                failure_error_function=None,
            )
            async with server:
                agent = self.agent_factory(
                    name="Tic-Tac-Toe AI Player",
                    model=self.settings.openai_model,
                    instructions=(
                        "You are the game-playing AI. Use only the provided game MCP tools. "
                        f"Play exactly one legal {current_player.value} move in game_id={game_id}. "
                        "First inspect the state with get_game_state. Then call make_move "
                        "with the requested index and actor='ai-agent'. Do not create a "
                        "different game, reset the game, or use tools outside this game."
                    ),
                    mcp_servers=[server],
                    mcp_config={
                        "convert_schemas_to_strict": True,
                        "failure_error_function": None,
                    },
                )
                await self.runner.run(
                    agent,
                    f"Make one move for game_id={game_id}.",
                )
        except Exception as exc:
            raise AgentTurnError("agent runtime failed") from exc

        after = self.store.get(game_id)
        if after.game.turn != before_turn + 1:
            raise AgentTurnError("agent did not make exactly one legal move")
        return after

    @staticmethod
    def _validate_turn(record: GameRecord) -> None:
        if record.mode is not GameMode.AI_VS_CPU:
            raise AgentTurnUnavailableError(
                "agent turns are only available for ai_vs_cpu games"
            )
        current_player = record.game.current_player
        if current_player is None or record.players.for_player(current_player) is not PlayerType.AI_AGENT:
            raise AgentTurnUnavailableError("agent turn is not currently available")
