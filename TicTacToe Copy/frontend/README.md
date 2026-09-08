# OpenHands Tic-Tac-Toe Frontend Demo

This frontend preserves the root app's FastAPI-backed game behavior and adds a
workflow panel that explains the Epic → Sprint → Task breakdown, agent write
zones, decisions, and verification evidence.

## Run

```bash
pnpm install
pnpm dev
```

The game API defaults to `http://127.0.0.1:8500`. Override it with
`VITE_API_URL` when the FastAPI service runs elsewhere.

## Verify

```bash
pnpm test
pnpm typecheck
pnpm lint
pnpm build
```

The workflow content is static presentation data. It does not expose Notion
credentials or call MCP directly from the browser.
