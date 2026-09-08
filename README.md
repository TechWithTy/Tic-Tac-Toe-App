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

## Continuous integration

The GitHub Actions workflow in [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
runs on pushes to `main` or `master` and on pull requests. It keeps the frontend and
backend checks independent so a failure is easy to localize.

The backend job locks the `uv` environment, runs Ruff, and executes the backend test
suite. The frontend job installs the locked pnpm dependencies, runs ESLint, executes
the frontend tests, checks TypeScript, and creates a production build.

The same checks can be run locally with the commands in [Verify](#verify). A local
workflow rehearsal is also available when `act` and Docker are installed:

```powershell
act -W .github/workflows/ci.yml -j backend -P ubuntu-latest=catthehacker/ubuntu:act-latest --container-architecture linux/amd64
```

## CodeQL security analysis

The [`.github/workflows/codeql.yml`](.github/workflows/codeql.yml) workflow runs
GitHub CodeQL security-extended analysis for both `python` and
`javascript-typescript` on pushes to `main` or `master`, pull requests, and a weekly
scheduled scan. Results are uploaded to GitHub code scanning when the workflow runs
in GitHub Actions.

The CodeQL CLI can also be used locally after installation. The JavaScript/TypeScript
scan targets the frontend, while the Python scan targets the first-party FastAPI code
under `backend/app`:

```powershell
codeql database create codeql-db-javascript --language=javascript-typescript --source-root frontend --overwrite
codeql database analyze codeql-db-javascript --format=sarif-latest --output=codeql-javascript.sarif --download

codeql database create codeql-db-python --language=python --source-root backend/app --overwrite
codeql database analyze codeql-db-python --format=sarif-latest --output=codeql-python.sarif --download
```

The local Python scan requires a Python launcher available to CodeQL. On Windows,
install Python 3.12 and ensure `py` or `python` is on `PATH`; WSL users can run the
same commands with the Linux CodeQL bundle. CodeQL is an additional security signal,
not a replacement for the project tests, Ruff, ESLint, TypeScript checks, or
production build.

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

To verify the container setup without starting the services, validate the Compose
file and build both images:

```powershell
docker compose config --quiet
docker compose build backend frontend
```

To verify the running stack, use `docker compose ps` and check that the backend is
healthy, then probe <http://localhost:8000/docs> and <http://localhost:8080/>. The
Compose setup exposes FastAPI on port `8000` and the Nginx-served frontend on port
`8080`.

Screen recording link: provided with the assignment submission.
