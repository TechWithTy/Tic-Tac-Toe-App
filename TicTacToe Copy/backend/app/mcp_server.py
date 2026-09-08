"""Constrained Light Speed MCP adapter for the canonical FastAPI game API."""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, RouteMap

APPROVED_TOOL_NAMES = frozenset(
    {"create_game", "get_game_state", "make_move", "reset_game"}
)

APPROVED_ROUTE_MAPS = [
    RouteMap(
        methods=["POST"],
        pattern=r"^/games$",
        mcp_type=MCPType.TOOL,
    ),
    RouteMap(
        methods=["GET"],
        pattern=r"^/games/\{game_id\}$",
        mcp_type=MCPType.TOOL,
    ),
    RouteMap(
        methods=["POST"],
        pattern=r"^/games/\{game_id\}/moves$",
        mcp_type=MCPType.TOOL,
    ),
    RouteMap(
        methods=["POST"],
        pattern=r"^/games/\{game_id\}/reset$",
        mcp_type=MCPType.TOOL,
    ),
    RouteMap(mcp_type=MCPType.EXCLUDE),
]


def build_mcp_server(api_app) -> FastMCP:
    """Build the MCP surface from the FastAPI OpenAPI contract."""
    return FastMCP.from_fastapi(
        app=api_app,
        name="Tic-Tac-Toe Game MCP",
        route_maps=APPROVED_ROUTE_MAPS,
    )
