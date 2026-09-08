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

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.instances.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
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


def make_service(store: GameStore, move_index: int | None = 4) -> tuple[AgentTurnService, FakeRunner]:
    runner = FakeRunner(store, move_index)
    service = AgentTurnService(
        settings=Settings(
            openai_api_key="test-key",
            light_speed_mcp_url="http://127.0.0.1:8000/mcp",
        ),
        store=store,
        server_factory=FakeMcpServer,
        agent_factory=FakeAgent,
        runner=runner,
    )
    return service, runner


@pytest.mark.parametrize("mode", ["ai_vs_ai", "ai_vs_human"])
def test_agent_turn_route_rejects_modes_other_than_ai_vs_cpu(mode: str):
    client = TestClient(app)
    game = client.post("/games", json={"mode": mode}).json()

    response = client.post(f"/games/{game['game_id']}/agent-turn")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "agent_turn_unavailable"
    assert client.get(f"/games/{game['game_id']}").json()["turn"] == 0


def test_settings_default_to_the_unified_fastapi_mcp_endpoint():
    assert str(Settings().light_speed_mcp_url) == "http://127.0.0.1:8000/mcp"


@pytest.mark.asyncio
async def test_agent_service_exposes_only_approved_mcp_tools_async():
    store = GameStore()
    game_id, _ = store.create(GameMode.AI_VS_CPU)
    FakeMcpServer.instances.clear()
    FakeAgent.instances.clear()
    service, _ = make_service(store)

    await service.run(game_id)

    assert FakeMcpServer.instances[0]["params"]["url"] == "http://127.0.0.1:8000/mcp"
    tool_filter = FakeMcpServer.instances[0]["tool_filter"]
    assert tool_filter["allowed_tool_names"] == list(APPROVED_AGENT_TOOLS)
    assert set(APPROVED_AGENT_TOOLS) == {
        "create_game",
        "get_game_state",
        "make_move",
        "reset_game",
    }


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
