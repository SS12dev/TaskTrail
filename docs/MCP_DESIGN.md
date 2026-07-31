# TaskTrail MCP Server — v1 Design & Architecture

Status: **Accepted** · Date: 2026-08-01 · Owner: Shivam

## 1. Goal

Expose TaskTrail's task/project management and AI planning capabilities to MCP clients
(Claude Desktop, Claude Code, etc.) so an LLM can manage the user's tasks conversationally.

## 2. Decisions (with rationale)

| Decision | Choice | Rationale |
|---|---|---|
| Integration | **Thin HTTP client over the existing REST API** | Backend stays the single source of truth for validation, auth, and business logic. No duplicated Firestore/service code. MCP server can evolve independently. |
| Auth | **Firebase refresh token via env config** | Single-user local server. The MCP server exchanges a long-lived refresh token for short-lived ID tokens via the Firebase Secure Token API, caches them, and refreshes ~5 min before expiry. No backend changes needed. |
| Transport | **stdio (local)** | Simplest v1; pairs with env-based auth. Code is transport-agnostic (FastMCP), so streamable HTTP is a config change later. |
| Language | **Python + FastMCP (official `mcp` SDK)** | Matches the backend stack; reuses domain vocabulary (statuses, priorities). |
| Scope | Task CRUD + search, Project CRUD, agent tool, resources & prompts | Full coverage of the API surface an LLM can meaningfully use. |

## 3. Architecture

```
Claude Desktop / Claude Code
        │  stdio (JSON-RPC / MCP)
        ▼
tasktrail_mcp (FastMCP, Python)
  ├─ auth.py      TokenManager: refresh token ──> ID token (cached, auto-refresh)
  ├─ client.py    Async httpx client → TaskTrail REST API (retry, error mapping)
  ├─ tools        tasks / projects / agent
  ├─ resources    tasktrail://today, tasktrail://projects, ...
  └─ prompts      daily_standup, weekly_review, plan_project
        │  HTTPS + Bearer <Firebase ID token>
        ▼
TaskTrail FastAPI backend (/api/v1) ──> Firestore
```

Not in the MCP path: the frontend, WebSockets, and the A2A layer. The LangGraph
multi-agent system is reached only through `POST /api/v1/agent/chat`.

## 4. Configuration

Environment variables (set in the MCP client config):

| Variable | Required | Description |
|---|---|---|
| `TASKTRAIL_API_URL` | no | Backend base URL (default `http://localhost:8000`) |
| `FIREBASE_WEB_API_KEY` | yes* | Firebase project Web API key (used for token refresh) |
| `FIREBASE_REFRESH_TOKEN` | yes* | User's refresh token (obtained once via login script) |
| `TASKTRAIL_ID_TOKEN` | no | Escape hatch: a raw ID token for quick testing (expires ≈1 h) |

\* not required if `TASKTRAIL_ID_TOKEN` is set.

A helper script (`mcp-server/scripts/get_refresh_token.py`) performs an
email/password sign-in against the Firebase Auth REST API and prints the refresh
token for one-time setup.

Example Claude Desktop config:

```json
{
  "mcpServers": {
    "tasktrail": {
      "command": "uv",
      "args": ["--directory", "/path/to/TaskTrail/mcp-server", "run", "tasktrail-mcp"],
      "env": {
        "TASKTRAIL_API_URL": "http://localhost:8000",
        "FIREBASE_WEB_API_KEY": "...",
        "FIREBASE_REFRESH_TOKEN": "..."
      }
    }
  }
}
```

## 5. Tool surface (v1)

All tools are prefixed `tasktrail_`. Inputs are Pydantic models; list tools support
`response_format` (`markdown` default, `json` for full payloads) and concise output
to protect context.

### Tasks

| Tool | Endpoint | Annotations |
|---|---|---|
| `tasktrail_create_task` | `POST /tasks/` | write |
| `tasktrail_list_tasks` | `GET /tasks/` (status, projectId, priority, tags, parentTaskId, includeCompleted) | read-only |
| `tasktrail_get_today_tasks` | `GET /tasks/today` | read-only |
| `tasktrail_get_task` | `GET /tasks/{id}` | read-only |
| `tasktrail_update_task` | `PATCH /tasks/{id}` (partial; also used to complete: `status="done"`) | write, idempotent |
| `tasktrail_delete_task` | `DELETE /tasks/{id}` | destructive |

### Projects

| Tool | Endpoint | Annotations |
|---|---|---|
| `tasktrail_create_project` | `POST /projects/` | write |
| `tasktrail_list_projects` | `GET /projects/` | read-only |
| `tasktrail_get_project` | `GET /projects/{id}` | read-only |
| `tasktrail_update_project` | `PATCH /projects/{id}` (archive via `isArchived=true`) | write, idempotent |
| `tasktrail_delete_project` | `DELETE /projects/{id}` | destructive |

### Agent

| Tool | Endpoint | Notes |
|---|---|---|
| `tasktrail_ask_agent` | `POST /agent/chat` | Delegates natural-language requests ("plan my week", "break down project X") to the backend LangGraph multi-agent system. Incurs LLM cost/latency — description tells the client to prefer direct CRUD tools for simple operations. |

Deliberately **excluded from v1**: `POST /tasks/{id}/reorder` (kanban drag-and-drop
positioning has no conversational use), auth routes, A2A routes, WebSockets.

### Domain enums (mirrored from backend models)

- status: `todo | in_progress | done | archived`
- priority: `low | medium | high | urgent`
- dueDate: ISO 8601 (`YYYY-MM-DD` or full datetime)

## 6. Resources & prompts

Resources (read-only snapshots, cheap context injection):

| URI | Content |
|---|---|
| `tasktrail://today` | Today view: due today, overdue, high-priority |
| `tasktrail://tasks` | Active (non-completed) tasks overview |
| `tasktrail://projects` | Projects with task counts |
| `tasktrail://projects/{project_id}/tasks` | Tasks for one project (template) |

Prompts:

| Name | Args | Purpose |
|---|---|---|
| `daily_standup` | — | Summarize today + overdue, propose a plan for the day |
| `weekly_review` | — | Review completed vs open, surface stalled tasks |
| `plan_project` | `project_description` | Break a goal into a project + tasks via the CRUD tools |

## 7. Error handling

`client.py` maps HTTP failures to actionable messages (never raw tracebacks):

- 401 → "Authentication failed — refresh token invalid/expired; re-run get_refresh_token.py"
- 404 → "Task/Project not found — verify the ID via tasktrail_list_*"
- 422 → surface FastAPI validation detail (field-level)
- Connection refused → "Backend unreachable at $TASKTRAIL_API_URL — is the FastAPI server running?"
- Timeout (30 s; 120 s for agent chat) → retry guidance

## 8. v2 candidates (explicitly out of scope)

Streamable HTTP + OAuth 2.1 for a hosted multi-user server; API-key auth in the
backend; reorder/kanban tools; write-through resources; subscription/notification
support for real-time updates; MCP evals in CI.
