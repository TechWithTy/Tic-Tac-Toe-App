# Tic-Tac-Toe

This repository contains a playable tic-tac-toe application built for the OpenHands take-home exercise. React, Vite, TypeScript, Tailwind, and Motion provide the frontend; FastAPI owns the canonical game state, validation, deterministic minimax CPU, and the constrained Light Speed MCP surface. The app supports Human vs Human, Human vs CPU, CPU vs CPU, and optional AI Agent pairings. Game completion is presented in an animated result modal, while all moves remain server-validated.

I used OpenAI Codex as an AI development partner to scaffold bounded slices, review implementation choices, write regression tests, and investigate integration issues. I retained ownership of the architecture and accepted changes only after reviewing diffs and running tests. With more time, I would add a live-key end-to-end test for the OpenAI agent, persistent game storage, and a hosted deployment. The runtime AI option is intentionally hidden when `OPENAI_API_KEY` is not configured.

## Run locally

Prerequisites: Node.js 24+, pnpm 9.15.9, Python 3.12+, and [uv](https://docs.astral.sh/uv/).

```powershell
# From the repository root
Copy-Item .env.example backend/.env

# Terminal 1: FastAPI and the mounted MCP server
Set-Location backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: React frontend
Set-Location frontend
pnpm install
pnpm dev
```

Open <http://localhost:5173>. FastAPI is available at <http://localhost:8000>; the MCP endpoint is <http://localhost:8000/mcp/>. Add an OpenAI key to `backend/.env` only when testing AI Agent mode. Without a key, the rest of the game remains playable and the AI Agent option is hidden.

## Verify

```powershell
# Frontend
Set-Location frontend
pnpm test
pnpm typecheck
pnpm lint
pnpm build

# Backend
Set-Location ..\backend
uv run ruff check app tests
uv run pytest tests -q
```

## Project structure

```text
frontend/       React/Vite client and UI tests
backend/        FastAPI app, game domain, minimax, MCP adapter, and tests
deploy/         Dockerfiles, Compose support, Nginx, and Kubernetes manifest
.github/        CI and CodeQL workflows
```

## Container run

```powershell
docker compose up --build
```

Open <http://localhost:8080>. See [deploy/README.md](deploy/README.md) for local-image Kubernetes notes. The application uses in-memory state; authentication, persistence, multiplayer networking, and production cluster provisioning are out of scope for this exercise.

Screen recording link: provided with the assignment submission.
