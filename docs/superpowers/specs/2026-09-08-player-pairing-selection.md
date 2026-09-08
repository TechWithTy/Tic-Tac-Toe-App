# Player Pairing Selection

## Goal

Allow the player to choose an independent controller for X and O, then explicitly start a game with that pairing.

## Approved design

- The frontend shows two labeled columns: Player X and Player O.
- Each column offers Human, CPU, and AI Agent.
- A Start game button creates the selected pairing; changing a selection does not create a game.
- FastAPI remains the canonical owner of game state, turn ownership, and move legality.
- The API accepts explicit `players: {x, o}` assignments and returns them with game state.
- Existing four-mode `mode` payloads remain accepted as a compatibility path.
- CPU turns are advanced through the existing server endpoint; AI turns are submitted through the constrained agent path.
- The frontend disables board actions when the current controller is CPU or AI Agent.

## Scope

The nine pairings are supported: Human/Human, Human/CPU, Human/AI Agent, CPU/Human, CPU/CPU, CPU/AI Agent, AI Agent/Human, AI Agent/CPU, and AI Agent/AI Agent. No database, networking, or new state-management dependency is introduced.
