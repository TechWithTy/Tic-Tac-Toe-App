# Player Pairing Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** Let players independently select Human, CPU, or AI Agent for X and O, then start any supported pairing through the canonical FastAPI game state.

**Architecture:** Add explicit X/O controller assignments to the FastAPI create/state contract while retaining legacy mode payload compatibility. React holds only pending selections and renders returned server state; it uses controller metadata to decide whether to show a human action affordance, call the CPU endpoint, or wait for the external AI-agent path.

**Tech Stack:** Python, FastAPI, pytest, React, Vite, TypeScript, Vitest, Testing Library, shadcn/ui, Magic UI, Playwright MCP.

**Spec:** `docs/superpowers/specs/2026-09-08-player-pairing-selection.md`

## Global Constraints

- FastAPI owns canonical game state, controller ownership, and move legality.
- React never calculates winners, legal moves, or turn validity.
- Existing four `mode` request values remain accepted for compatibility.
- No new runtime dependency, database, authentication, or infrastructure work.
- The AI-agent runtime retains only the approved MCP game tools.
- Each task must have a failing behavioral test before production code.

---

### Task 1: Extend the FastAPI game contract to explicit player assignments

**Files:**
- Modify: `backend/app/store.py`
- Modify: `backend/app/api/games.py`
- Modify: `backend/app/agent_service.py`
- Test: `backend/tests/test_api.py`
- Test: `backend/tests/test_agent.py`
- Test: `backend/tests/test_mcp.py`

**Interfaces:**
- Add `PlayerType` values `human`, `cpu`, and `ai-agent`.
- Add `PlayerAssignments` with `x: PlayerType` and `o: PlayerType`.
- `POST /games` accepts `{"players":{"x":"human","o":"ai-agent"}}` and returns `players` in the game state.
- Legacy `{"mode":"human_vs_cpu"}` maps to `{"x":"human","o":"cpu"}`.
- `GameRecord.players` is the source used by CPU and AI turn validation.

- [ ] **Step 1: Write failing API tests** for all-new assignment payloads, returned assignments, CPU/Human and Human/AI turn ownership, and legacy mode compatibility.
- [ ] **Step 2: Run targeted tests** with `uv run pytest backend/tests/test_api.py -q` and confirm failures are caused by missing assignment support. If dependency resolution is blocked, record the exact environment error and continue with available checks.
- [ ] **Step 3: Implement the minimal assignment model** in the store and request/response schemas. Derive the legacy `mode` response from assignments so existing clients remain readable.
- [ ] **Step 4: Route CPU ownership through `GameRecord.players[current_player]`** and route agent-turn validation through the same assignment map; do not add rule logic to the frontend.
- [ ] **Step 5: Update MCP/agent tests and schemas** so `create_game` exposes explicit players while approved tool names and server-side validation remain unchanged.
- [ ] **Step 6: Run targeted backend tests** and verify the new pairing cases plus all existing game invariants pass.

### Task 2: Add typed frontend player assignments and API mapping

**Files:**
- Modify: `frontend/src/types/game.ts`
- Modify: `frontend/src/api/game-api.ts`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Add `PlayerType = "human" | "cpu" | "ai-agent"`.
- Add `PlayerSelection = { x: PlayerType; o: PlayerType }`.
- Change `GameApi.createGame` to `createGame(players: PlayerSelection): Promise<GameState>`.
- The API adapter sends `{players:{x,o}}`, maps snake_case state, and preserves returned `players`.

- [ ] **Step 1: Write failing adapter/UI tests** asserting Start game sends the selected X/O values and does not create a game when only a selector changes.
- [ ] **Step 2: Run the focused frontend test** and confirm it fails because the current API accepts only a single legacy mode and creates on selection change.
- [ ] **Step 3: Implement the explicit assignment types and fetch mapping** without changing game-rule behavior.
- [ ] **Step 4: Run the focused frontend tests** and verify selected assignment payloads and returned controller metadata.

### Task 3: Replace the mode list with two player columns and Start game flow

**Files:**
- Create: `frontend/src/components/player-selector.tsx`
- Modify: `frontend/src/components/mode-options.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/game-board.tsx` only if accessible status text needs a focused prop addition
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- `PlayerSelector` receives `player: "x" | "o"`, `value: PlayerType`, and `onChange(value: PlayerType)`.
- App maintains `pendingPlayers` independently from `gameState`.
- Start button calls `createGame(pendingPlayers)` once and only then activates the returned board.

- [ ] **Step 1: Write failing UI tests** for two selector columns, Human/CPU/AI Agent options, no request on selection change, Start game request, and accessible labels.
- [ ] **Step 2: Run the focused frontend tests** and confirm the current single mode selector fails the new interaction contract.
- [ ] **Step 3: Implement the two-column selectors** using semantic fieldsets/radios, clear X/O labels, and the existing restrained design system.
- [ ] **Step 4: Implement Start game, loading, error, and reset behavior** while keeping pending selections separate from server state.
- [ ] **Step 5: Run frontend tests, typecheck, lint, and build**.

### Task 4: Coordinate CPU and human affordances for every pairing

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- CPU advancement is allowed only when the returned state says the current player is controlled by CPU.
- Board input is enabled only when the returned current player is controlled by Human.
- AI-controlled turns show a wait message and never call `/cpu-move` or submit a human move.

- [ ] **Step 1: Write failing tests** for Human/CPU, CPU/Human, CPU/AI, AI/Human, and AI/CPU control transitions using server-shaped fixtures.
- [ ] **Step 2: Run the tests** and confirm current mode-based orchestration cannot represent the new combinations.
- [ ] **Step 3: Replace mode checks with returned controller checks** and preserve StrictMode request deduplication.
- [ ] **Step 4: Run the full frontend test suite** and verify all pairing transitions remain server-driven.

### Task 5: Independent browser verification and review evidence

**Files:**
- Modify: `README.md` only if the start flow needs a user-facing run instruction
- Update: Notion task `Verify agent coordination and Playwright critical flows`

- [ ] **Step 1: Start the API and frontend using the repository run instructions.**
- [ ] **Step 2: Run Playwright scenarios** for load, selector accessibility, Start game, Human/Human first move, Human/CPU CPU response, CPU/CPU completion, reset, and disabled AI turns.
- [ ] **Step 3: Inspect network requests** to confirm the explicit X/O assignment payload and server endpoints.
- [ ] **Step 4: Record any observed failure before remediation** and keep QA changes separate from implementation changes.
- [ ] **Step 5: Update the Notion task** with evidence, blockers, and human acceptance status.
