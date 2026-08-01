# mcp-server/CLAUDE.md

Python FastMCP-style server (`mcp` SDK's `MCPServer`, formerly `FastMCP`)
exposing the TaskTrail backend REST API to MCP clients. Read
`docs/MCP_DESIGN.md` (repo root) before changing scope, auth, or transport —
those are deliberate v1 decisions, not defaults.

## Commands

```bash
uv sync                      # install deps (incl. dev extras)
uv run tasktrail-mcp         # run over stdio
uv run pytest                # tests, all mocked — no live backend needed
uv run ruff check .          # lint
```

## Hard rule: this package never imports backend code or touches Firestore

Everything goes through `client.py` (`httpx.AsyncClient` → `/api/v1/*`). If
you find yourself wanting to import from `backend/app`, stop — either the
functionality belongs behind a REST endpoint (add it to the backend first) or
it doesn't belong in this package.

## Layout

```
src/tasktrail_mcp/
  config.py     Settings (pydantic-settings, env-driven) — see Settings docstring for auth modes
  auth.py       TokenManager — Firebase refresh token -> cached ID token
  client.py     TaskTrailClient — the only thing that calls httpx; maps HTTP
                errors to actionable messages (see docstrings in client.py,
                never let a raw traceback reach the MCP client)
  formatting.py Markdown renderers for task/project lists (default output;
                response_format="json" bypasses this)
  tools/        One module per resource family (tasks.py, projects.py,
                agent.py); each exposes register(mcp) — called from server.py
  resources.py  tasktrail:// read-only resources
  prompts.py    Prompt templates (return a user-message string; they don't
                call the API themselves, they instruct the client's model to
                use the tools)
  server.py     Builds the MCPServer instance, registers everything, main()
```

## Adding a tool

1. Confirm the backend endpoint exists (`backend/app/routes/`) — don't invent
   API surface here.
2. Add the method to `client.py` only if it's a new HTTP verb/path shape;
   otherwise reuse `client.get/post/patch/delete`.
3. Write the tool in the relevant `tools/*.py` module, registered via that
   module's `register(mcp)`. Use `ToolAnnotations` (readOnlyHint /
   destructiveHint / idempotentHint) matching the table in
   `docs/MCP_DESIGN.md` section 5.
4. Docstring is the tool description shown to the LLM — be specific about
   what it does, valid enum values, and when to prefer it over
   `tasktrail_ask_agent` or vice versa.
5. Field names stay camelCase (`dueDate`, `projectId`) to match the backend
   API — same rule as `backend/CLAUDE.md`.
6. Update `docs/MCP_DESIGN.md`'s tool table and add a test.

## Testing

No live backend in CI or by default locally — `tests/` mocks `httpx` (see
`tests/conftest.py`) so the suite runs offline. If you do want to smoke-test
against a real backend, run `uvicorn app.main:app` from `backend/` first, get
a refresh token via `scripts/get_refresh_token.py`, and run `uv run
tasktrail-mcp` manually or via the MCP inspector.

## Gotchas

- The `mcp` SDK's ergonomic server class is `mcp.server.mcpserver.MCPServer`
  (imported as `MCPServer` in this codebase) — older docs/examples calling it
  `FastMCP` from `mcp.server.fastmcp` refer to a pre-2.0 SDK layout that no
  longer exists; don't reintroduce that import path.
- `settings` in `config.py` is a module-level singleton, same pattern as
  `client` in `client.py` and `token_manager` in `auth.py` — import and use
  them directly, don't re-instantiate.
- Never commit `.env` (already gitignored) or print/log the refresh or ID
  token.
