# Backend

The FastAPI application owns canonical game state and exposes the approved Light Speed MCP game tools at `/mcp`. The runtime AI player connects to that MCP surface through the OpenAI Agents SDK; it never receives direct access to the `GameStore`.

## Local configuration

The expected local environment file is `backend/.env`:

```powershell
Set-Location backend
Copy-Item ..\.env.example .env
```

Set `OPENAI_API_KEY` locally. Keep `backend/.env` untracked. `OPENAI_MODEL` and the Light Speed MCP URL/transport are configurable through the same file. The default MCP URL is the unified API process at `http://127.0.0.1:8000/mcp`.

Start the unified API and MCP server from `backend/`:

```powershell
uv run uvicorn app.main:app --reload --port 8000
```

No second MCP process is required. The same FastAPI process serves the API and the constrained MCP surface.

The AI turn endpoint is `POST /games/{game_id}/agent-turn`. It is only available for `ai_vs_cpu` games while X is the current player. The endpoint returns safe structured errors when configuration, MCP connectivity, or the proposed move fails.
