"""CLI entry point for the unified Tic-Tac-Toe API and MCP server."""

import uvicorn

from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8500)
