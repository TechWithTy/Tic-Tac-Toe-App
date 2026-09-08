import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from app.main import app
from app.mcp_server import build_mcp_server


@pytest.mark.asyncio
async def test_mcp_exposes_only_the_approved_game_tools():
    server = build_mcp_server(app)

    async with Client(server) as client:
        tools = await client.list_tools()

    assert {tool.name for tool in tools} == {
        "create_game",
        "get_game_state",
        "make_move",
        "reset_game",
    }


@pytest.mark.asyncio
async def test_mcp_delegates_validation_reset_and_audit_to_fastapi(caplog):
    caplog.set_level(logging.INFO, logger="tic_tac_toe.audit")
    server = build_mcp_server(app)

    async with Client(server) as client:
        created = await client.call_tool("create_game", {"mode": "ai_vs_cpu"})
        game_id = created.data.game_id

        accepted = await client.call_tool(
            "make_move",
            {"game_id": game_id, "index": 0, "actor": "ai-agent"},
        )
        rejected = await client.call_tool(
            "make_move",
            {"game_id": game_id, "index": 1, "actor": "human"},
            raise_on_error=False,
        )
        state = await client.call_tool("get_game_state", {"game_id": game_id})
        reset = await client.call_tool("reset_game", {"game_id": game_id})

    assert accepted.data.board[0] == "X"
    assert rejected.is_error is True
    assert state.data.board[0] == "X"
    assert state.data.board[1] is None
    assert reset.data.board == [None] * 9

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "tic_tac_toe.audit"
    ]
    assert events[-2:] == [
        {
            "accepted": True,
            "actor": "ai-agent",
            "game_id": game_id,
            "requested_move": 0,
            "tool": "make_move",
            "turn": 1,
        },
        {
            "accepted": False,
            "actor": "human",
            "game_id": game_id,
            "requested_move": 1,
            "tool": "make_move",
            "turn": 1,
        },
    ]


@pytest.mark.asyncio
async def test_api_and_mcp_share_the_canonical_runtime_store():
    api_client = TestClient(app)
    created = api_client.post("/games", json={"mode": "ai_vs_cpu"})
    game_id = created.json()["game_id"]
    mcp_server = getattr(app.state, "mcp_server", None)

    assert any(getattr(route, "path", None) == "/mcp" for route in app.routes)
    assert mcp_server is not None

    async with Client(mcp_server) as client:
        state = await client.call_tool("get_game_state", {"game_id": game_id})
        moved = await client.call_tool(
            "make_move",
            {"game_id": game_id, "index": 0, "actor": "ai-agent"},
        )

    assert state.data.game_id == game_id
    assert state.data.board == [None] * 9
    assert moved.data.board[0] == "X"


@pytest.mark.asyncio
async def test_mounted_http_mcp_endpoint_shares_api_state():
    def httpx_client_factory(**kwargs):
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            **kwargs,
        )

    with TestClient(app) as api_client:
        created = api_client.post("/games", json={"mode": "ai_vs_cpu"})
        game_id = created.json()["game_id"]
        transport = StreamableHttpTransport(
            "http://testserver/mcp/",
            httpx_client_factory=httpx_client_factory,
        )

        async with Client(transport) as client:
            state = await client.call_tool("get_game_state", {"game_id": game_id})
            moved = await client.call_tool(
                "make_move",
                {"game_id": game_id, "index": 0, "actor": "ai-agent"},
            )

    assert state.data.game_id == game_id
    assert state.data.board == [None] * 9
    assert moved.data.board[0] == "X"
