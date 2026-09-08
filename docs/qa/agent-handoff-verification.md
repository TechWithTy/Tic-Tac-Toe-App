# Agent Handoff Verification

This QA artifact verifies the runtime boundary for the AI player.

## Scope

- The browser selects an AI-controlled player through the normal setup UI.
- The frontend calls the FastAPI agent-turn endpoint.
- FastAPI remains responsible for game state, turn ownership, move legality, and the returned canonical state.
- The agent receives only the constrained game capability surface; shell and filesystem access are not part of the game-playing runtime.

## Verification procedure

1. Start FastAPI and the Vite frontend with the configured MCP/OpenAI runtime.
2. Select AI Agent for X and CPU or Human for O.
3. Start the game.
4. Inspect the network request to `POST /games/{game_id}/agent-turn`.
5. Confirm the response is successful and contains the accepted move in canonical state.
6. Confirm the rendered board matches the response.
7. Repeat with an invalid or unavailable turn and confirm the server rejects it without mutating state.

## Evidence captured

- Live `/agent-turn` request returned HTTP 200.
- The accepted agent move appeared in the rendered board.
- Backend regression suite passed.
- No client-side legality engine was added.

## QA disposition

This is review evidence only. Human acceptance is required before merging the associated implementation PRs.
