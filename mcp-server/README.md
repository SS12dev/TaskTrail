# tasktrail-mcp

MCP server exposing the [TaskTrail](../README.md) task-management API to MCP
clients (Claude Desktop, Claude Code, etc.) over stdio.

Design and architecture decisions: [`docs/MCP_DESIGN.md`](../docs/MCP_DESIGN.md).

## What it does

A thin async HTTP client over TaskTrail's `/api/v1` REST API — no direct
Firestore or backend code access. It authenticates as a single TaskTrail user
via a Firebase refresh token, and exposes that user's tasks/projects (plus the
backend's own AI planning agent) as MCP tools, resources, and prompts.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a running TaskTrail backend
(see the [backend README](../backend)).

```bash
cd mcp-server
uv sync                              # installs deps incl. dev extras into .venv
uv run python scripts/get_refresh_token.py   # one-time: prints a Firebase refresh token
```

Copy `.env.example` to `.env` and fill in the values (or set the same as
environment variables in your MCP client config — see below):

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `TASKTRAIL_API_URL` | no | Backend base URL (default `http://localhost:8000`) |
| `FIREBASE_WEB_API_KEY` | yes* | Firebase project Web API key |
| `FIREBASE_REFRESH_TOKEN` | yes* | From `get_refresh_token.py` |
| `TASKTRAIL_ID_TOKEN` | no | Escape hatch: raw ID token for quick testing (expires ~1h) |

\* not required if `TASKTRAIL_ID_TOKEN` is set.

## Running

```bash
uv run tasktrail-mcp
```

Runs over stdio — it's meant to be launched by an MCP client, not used
interactively. To point Claude Desktop at it, add to its config:

```json
{
  "mcpServers": {
    "tasktrail": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/TaskTrail/mcp-server", "run", "tasktrail-mcp"],
      "env": {
        "TASKTRAIL_API_URL": "http://localhost:8000",
        "FIREBASE_WEB_API_KEY": "...",
        "FIREBASE_REFRESH_TOKEN": "..."
      }
    }
  }
}
```

## Development

```bash
uv run ruff check .      # lint
uv run pytest            # tests (all mocked — no live backend required)
```

See [`../mcp-server/CLAUDE.md`](./CLAUDE.md) for conventions when adding
tools/resources/prompts.
