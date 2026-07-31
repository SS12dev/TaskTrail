## What & why

<!-- What does this PR change, and what problem does it solve? Link issues: Closes #123 -->

## Area

- [ ] backend (FastAPI / services / agents)
- [ ] frontend (React)
- [ ] mcp-server
- [ ] docs / CI

## How was it tested?

<!-- Commands run, manual steps, screenshots for UI changes -->

## Checklist

- [ ] Follows layering rules (routes → services → Firestore; no Firestore in routes; frontend HTTP only via `src/services/`)
- [ ] All Firestore queries filter by `userId`
- [ ] API field names stay camelCase; TS types updated in lockstep with Pydantic models (if API changed)
- [ ] `docs/MCP_DESIGN.md` updated if the MCP tool surface changed
- [ ] No secrets committed (`.env`, `serviceAccountKey.json`)
