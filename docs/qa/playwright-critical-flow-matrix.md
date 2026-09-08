# Playwright Critical-Flow Matrix

This matrix is the deterministic browser QA contract for the tic-tac-toe client.

| Scenario | Expected evidence |
| --- | --- |
| Application load | FastAPI connection state is visible and no console errors are emitted |
| Independent selectors | X and O each expose Human, CPU, and AI Agent controls |
| Explicit start | Start game sends the selected X/O assignment and renders returned server state |
| First move | X starts and the first accepted mark is visible |
| Alternation | After X, the UI reports O to move |
| Occupied cell | An occupied cell remains disabled and cannot be overwritten |
| Completion | A winner or draw is visible and the board stops accepting moves |
| Reset | Reset returns the UI to setup with a fresh board |
| Human vs CPU | Human move is rendered immediately, then the CPU response is rendered |
| CPU vs CPU | Automated play completes to a visible terminal state |
| AI handoff | Agent-turn request succeeds and the accepted agent move is rendered |
| Responsive/accessibility | User-facing roles, labels, keyboard controls, and readable state text remain available |

## Execution rules

- Use isolated scenarios and controlled game state.
- Prefer `getByRole`, labels, and observable state over CSS selectors.
- Await observable conditions instead of arbitrary sleeps.
- Record failures before remediation.
- Browser Use is exploratory-only and does not duplicate this matrix.
- A review is not a merge approval until required evidence is repeatable and no P0/P1 defect remains.

## Captured result

The current live review passed the listed core flows, including CPU-vs-CPU draw completion, AI handoff, and zero console errors. An initial strict locator ambiguity around the phrase "Round complete" was scoped to the result dialog and documented as a test-harness correction, not an application defect.
