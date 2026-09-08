import asyncio
import json
from types import SimpleNamespace
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from app.agent_service import (
    APPROVED_AGENT_TOOLS,
    AgentTurnService,
    AgentTurnUnavailableError,
)
from app.api import games
from app.main import app
from app.settings import Settings
from app.store import GameMode, GameStore


class FakeMcpServer:
    instances: ClassVar[list[dict]] = []
    enters: ClassVar[int] = 0
    exits: ClassVar[int] = 0

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.instances.append(kwargs)

    async def __aenter__(self):
        type(self).enters += 1
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        type(self).exits += 1
        return False


class FakeAgent:
    instances: ClassVar[list[dict]] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.instances.append(kwargs)


class FakeRunner:
    def __init__(self, store: GameStore, move_index: int | None):
        self.store = store
        self.move_index = move_index
        self.calls: list[tuple[object, str]] = []

    async def run(self, agent, prompt):
        self.calls.append((agent, prompt))
        if self.move_index is not None:
            game_id = prompt.rsplit("game_id=", 1)[1].rstrip(".")
            self.store.make_move(game_id, self.move_index)
        return SimpleNamespace(final_output="done")


class BlockingRunner:
    def __init__(self, store: GameStore, move_index: int):
        self.store = store
        self.move_index = move_index
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.active = 0
        self.max_active = 0

    async def run(self, agent, prompt):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.started.set()
        await self.release.wait()
        game_id = prompt.rsplit("game_id=", 1)[1].rstrip(".")
        self.store.make_move(game_id, self.move_index)
        self.active -= 1
        return SimpleNamespace(final_output="done")


class FailOnceRunner:
    def __init__(self, store: GameStore, move_index: int):
        self.store = store
        self.move_index = move_index
        self.calls = 0

    async def run(self, agent, prompt):
        self.calls += 1
        if self.calls == 1:
            raise ConnectionError("MCP connection lost")
        game_id = prompt.rsplit("game_id=", 1)[1].rstrip(".")
        self.store.make_move(game_id, self.move_index)
        return SimpleNamespace(final_output="done")


def make_service(store: GameStore, move_index: int | None = 4) -> tuple[AgentTurnService, FakeRunner]:
    runner = FakeRunner(store, move_index)
    service = AgentTurnService(
        settings=Settings(
            openai_api_key="test-key",
            light_speed_mcp_url="http://127.0.0.1:8500/mcp",
        ),
        store=store,
        server_factory=FakeMcpServer,
        agent_factory=FakeAgent,
        runner=runner,
    )
    return service, runner


@pytest.mark.parametrize("mode", ["human_vs_human", "cpu_vs_human"])
def test_agent_turn_route_rejects_when_current_player_is_not_ai_agent(mode: str):
    client = TestClient(app)
    game = client.post("/games", json={"mode": mode}).json()

    response = client.post(f"/games/{game['game_id']}/agent-turn")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "agent_turn_unavailable"
    assert client.get(f"/games/{game['game_id']}").json()["turn"] == 0


def test_settings_default_to_the_unified_fastapi_mcp_endpoint(monkeypatch):
    monkeypatch.delenv("LIGHT_SPEED_MCP_URL", raising=False)
    assert str(Settings(_env_file=None).light_speed_mcp_url) == "http://127.0.0.1:8500/mcp"


@pytest.mark.asyncio
async def test_agent_service_exposes_only_approved_mcp_tools_async():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_CPU)
    FakeMcpServer.instances.clear()
    FakeAgent.instances.clear()
    service, _ = make_service(store)

    await service.run(game_id)

    assert FakeMcpServer.instances[0]["params"]["url"] == "http://127.0.0.1:8500/mcp/"
    tool_filter = FakeMcpServer.instances[0]["tool_filter"]
    assert tool_filter["allowed_tool_names"] == list(APPROVED_AGENT_TOOLS)
    assert set(APPROVED_AGENT_TOOLS) == {
        "create_game",
        "get_game_state",
        "make_move",
        "reset_game",
    }


@pytest.mark.asyncio
async def test_agent_service_reuses_connected_mcp_server_and_agent():
    store = GameStore()
    first_game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    second_game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    FakeMcpServer.instances.clear()
    FakeMcpServer.enters = 0
    FakeMcpServer.exits = 0
    FakeAgent.instances.clear()
    runner = FakeRunner(store, move_index=4)
    service = AgentTurnService(
        settings=Settings(openai_api_key="test-key"),
        store=store,
        server_factory=FakeMcpServer,
        agent_factory=FakeAgent,
        runner=runner,
    )

    await service.run(first_game_id)
    await service.run(second_game_id)

    assert len(FakeMcpServer.instances) == 1
    assert FakeMcpServer.enters == 1
    assert FakeMcpServer.exits == 0
    assert len(FakeAgent.instances) == 1
    assert runner.calls[0][0] is runner.calls[1][0]

    await service.close()

    assert FakeMcpServer.exits == 1


@pytest.mark.asyncio
async def test_agent_service_serializes_concurrent_turns_for_the_same_game():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    runner = BlockingRunner(store, move_index=4)
    service = AgentTurnService(
        settings=Settings(openai_api_key="test-key"),
        store=store,
        server_factory=FakeMcpServer,
        agent_factory=FakeAgent,
        runner=runner,
    )

    first = asyncio.create_task(service.run(game_id))
    await asyncio.wait_for(runner.started.wait(), timeout=1)
    second = asyncio.create_task(service.run(game_id))
    await asyncio.sleep(0)

    assert runner.max_active == 1
    assert not second.done()

    runner.release.set()
    first_result, second_result = await asyncio.gather(
        first,
        second,
        return_exceptions=True,
    )

    assert not isinstance(first_result, Exception)
    assert isinstance(second_result, Exception)
    assert runner.max_active == 1
    assert store.get(game_id).game.turn == 1
    assert service._game_locks == {}


@pytest.mark.asyncio
async def test_agent_service_reconnects_after_a_runner_failure():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    FakeMcpServer.instances.clear()
    FakeMcpServer.enters = 0
    FakeMcpServer.exits = 0
    runner = FailOnceRunner(store, move_index=4)
    service = AgentTurnService(
        settings=Settings(
            openai_api_key="test-key",
            light_speed_mcp_url="http://127.0.0.1:8500/mcp",
        ),
        store=store,
        server_factory=FakeMcpServer,
        agent_factory=FakeAgent,
        runner=runner,
    )

    with pytest.raises(RuntimeError, match="agent runtime failed"):
        await service.run(game_id)

    assert FakeMcpServer.enters == 1
    assert FakeMcpServer.exits == 1

    state = await service.run(game_id)

    assert state.game.turn == 1
    assert FakeMcpServer.enters == 2
    assert FakeMcpServer.exits == 1
    await service.close()
    assert FakeMcpServer.exits == 2


@pytest.mark.asyncio
async def test_agent_service_prunes_completed_game_locks():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    service, _ = make_service(store)

    await service.run(game_id)

    assert service._game_locks == {}
    await service.close()


@pytest.mark.asyncio
async def test_agent_service_logs_latency_for_a_successful_turn(caplog: pytest.LogCaptureFixture):
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    service, _ = make_service(store)

    with caplog.at_level("INFO", logger="tic_tac_toe.agent"):
        await service.run(game_id)

    event = json.loads(next(record.message for record in caplog.records if record.name == "tic_tac_toe.agent"))
    assert event["event"] == "agent_turn_latency"
    assert event["game_id"] == game_id
    assert event["success"] is True
    assert event["mcp_session_reused"] is False
    assert event["agent_setup_ms"] >= 0
    assert event["runner_ms"] >= 0
    assert event["total_ms"] >= 0


@pytest.mark.asyncio
async def test_agent_service_accepts_the_ai_turn_when_ai_is_o_in_cpu_vs_ai_mode():
    store = GameStore()
    game_id, _ = store.create(GameMode.CPU_VS_AI)
    store.advance_cpu(game_id)
    service, _ = make_service(store, move_index=4)

    await service.run(game_id)

    record = store.get(game_id)
    assert record.game.turn == 2
    assert record.game.board[4].value == "O"


@pytest.mark.asyncio
async def test_agent_service_accepts_the_ai_turn_against_a_human():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_HUMAN)
    service, _ = make_service(store, move_index=4)

    await service.run(game_id)

    record = store.get(game_id)
    assert record.game.turn == 1
    assert record.game.current_player.value == "O"
    assert record.game.board[4].value == "X"


@pytest.mark.asyncio
async def test_agent_service_rejects_non_ai_vs_cpu_without_connecting_to_mcp():
    store = GameStore()
    game_id, _ = store.create(GameMode.HUMAN_VS_HUMAN)
    FakeMcpServer.instances.clear()
    service, _ = make_service(store)

    with pytest.raises(AgentTurnUnavailableError):
        await service.run(game_id)

    assert FakeMcpServer.instances == []
    assert store.get(game_id).game.turn == 0


@pytest.mark.asyncio
async def test_agent_service_preserves_state_when_agent_does_not_make_a_move():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_CPU)
    service, _ = make_service(store, move_index=None)

    with pytest.raises(RuntimeError, match="did not make exactly one legal move"):
        await service.run(game_id)

    record = store.get(game_id)
    assert record.game.turn == 0
    assert record.game.board == (None,) * 9


@pytest.mark.asyncio
async def test_agent_service_returns_safe_error_and_preserves_state_for_invalid_move():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_CPU)
    store.make_move(game_id, 4)
    store.advance_cpu(game_id)
    before = store.get(game_id).game.board
    service, _ = make_service(store, move_index=4)

    with pytest.raises(RuntimeError, match="agent runtime failed"):
        await service.run(game_id)

    assert store.get(game_id).game.board == before


def test_agent_turn_route_returns_structured_configuration_error_without_mutating_state(
    monkeypatch: pytest.MonkeyPatch,
):
    client = TestClient(app)
    original_service = games.agent_turn_service
    store = games.store
    game = client.post("/games", json={"mode": "ai_vs_cpu"}).json()
    monkeypatch.setattr(
        games,
        "agent_turn_service",
        AgentTurnService(settings=Settings(openai_api_key=None), store=store),
    )

    try:
        response = client.post(f"/games/{game['game_id']}/agent-turn")
    finally:
        monkeypatch.setattr(games, "agent_turn_service", original_service)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "agent_configuration_missing"
    assert client.get(f"/games/{game['game_id']}").json()["turn"] == 0
