# backend/CLAUDE.md

FastAPI backend. Run: `uvicorn app.main:app --reload --port 8000` (needs `.env` and `serviceAccountKey.json` in this directory).

## Layering rules (strict)

```
routes/  →  services/  →  Firestore (via app.firebase.get_firestore_client)
             ▲
agents/tools/ (LangChain @tool wrappers call the same services)
```

- Routes: HTTP concerns only — parse params, `Depends(get_current_user)`, delegate to a service. No Firestore access in routes.
- Services: all business logic. Instantiate per request (`TaskService()`), raise `HTTPException` with proper status codes.
- Every Firestore query MUST filter by `userId`. A missing filter is a cross-tenant data leak.

## Adding an endpoint

1. Pydantic models in `app/models/` — request (`XCreate`/`XUpdate`, all-optional for update) and response (`XResponse` with `id`, `userId`, timestamps).
2. Service method in `app/services/` with docstring + type hints.
3. Route in `app/routes/`, registered in `app/main.py` with prefix `/api/v1`.
4. If agents should use it, add a `@tool` wrapper in `app/agents/tools/` and register it with the relevant agent.

## Gotchas

- API field names are camelCase (`dueDate`, `projectId`) — matches frontend and existing Firestore docs. Don't "fix" to snake_case.
- `firestore.SERVER_TIMESTAMP` for `createdAt`/`updatedAt`; `completedAt` is set automatically when status → `done` (see `TaskService.update_task`).
- Task `position` is managed server-side (`_get_next_position`) for kanban ordering.
- Config via `app/config.py` (pydantic-settings, reads `.env`). New settings get typed fields there, never inline `os.environ`.
- Agent LLM calls use `openai_api_key` / `openai_model` from settings; agent code lives in `app/agents/`, orchestrated by `multi_agent_system.py` (LangGraph supervisor pattern).
- `routes/test.py` is scratch/testing — don't build on it.
