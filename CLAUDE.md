# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

TaskTrail — AI-powered task manager. Three deployable parts:

- `backend/` — FastAPI + Firestore + LangGraph multi-agent system (Python 3.10+)
- `frontend/` — React 19 + TypeScript + Vite + Tailwind 4 + Zustand
- `mcp-server/` — Python FastMCP server exposing the backend REST API to MCP clients (stdio)

Design doc for the MCP server: `docs/MCP_DESIGN.md` — read it before changing anything in `mcp-server/`.

## Commands

```bash
# Backend (from backend/, needs .env + serviceAccountKey.json)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000     # API at :8000, docs at /docs

# Frontend (from frontend/)
npm install
npm run dev        # Vite dev server, :5173
npm run build      # tsc -b && vite build (type-checks)
npm run lint       # eslint

# MCP server (from mcp-server/)
pip install -e ".[dev]"
tasktrail-mcp                                  # run over stdio
pytest                                         # tests
```

There is no backend test suite yet; verify backend changes by running the server and hitting `/docs`.

## Architecture — the parts that matter

**Request flow:** frontend (axios, Firebase ID token in `Authorization: Bearer`) → FastAPI routes (`backend/app/routes/`) → services (`backend/app/services/`) → Firestore. Routes never touch Firestore directly; all business logic lives in services (`TaskService`, `ProjectService`). The MCP server follows the same contract: it is a pure HTTP client of the REST API, never imports backend code.

**Auth:** every protected route uses `Depends(get_current_user)` (`backend/app/dependencies.py`), which verifies a Firebase ID token. User isolation is by `userId` field on every Firestore doc — services must always filter by it.

**Agent system** (`backend/app/agents/`): LangGraph supervisor pattern — supervisor routes to planner / executor / query / conversation agents. Agents call the same services via LangChain tool wrappers in `agents/tools/`. Entry point: `POST /api/v1/agent/chat`.

**A2A layer** (`backend/app/a2a/`, `routes/a2a.py`): agent-to-agent protocol + WebSocket manager. Mounted without the `/api/v1` prefix. Don't touch unless the task is explicitly about A2A.

**API conventions:** base prefix `/api/v1`. Field names are camelCase in API payloads (`dueDate`, `projectId`, `isArchived`) even in Python — keep it that way, the frontend and Firestore docs depend on it. Task status: `todo | in_progress | done | archived`. Priority: `low | medium | high | urgent`.

## Conventions

- Python: PEP 8, type hints everywhere, docstrings on public functions (see CONTRIBUTING.md). Pydantic v2 (`model_config`, `model_dump()`, `field_validator`).
- TypeScript: functional components + hooks, types in `frontend/src/types/`, API calls in `frontend/src/services/`, state in Zustand stores (`frontend/src/stores/`).
- Never commit `serviceAccountKey.json` or `.env` (already gitignored).
- Secrets/config go through `backend/app/config.py` (pydantic-settings), not raw `os.environ`.

## Per-directory notes

More specific guidance lives in `backend/CLAUDE.md`, `frontend/CLAUDE.md`, and `mcp-server/CLAUDE.md`.
