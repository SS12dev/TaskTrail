# frontend/CLAUDE.md

React 19 + TypeScript + Vite 7 + Tailwind 4. Run: `npm run dev`. Always verify with `npm run build` (runs `tsc -b`) before considering a change done — there are no frontend tests.

## Structure

- `src/pages/` — route-level components (Dashboard, Tasks, Kanban, Calendar, Today, Agent, auth pages). Routing in `App.tsx` (React Router v7), protected by `components/auth/ProtectedRoute`.
- `src/components/` — grouped by feature (`tasks/`, `kanban/`, `calendar/`, `auth/`, `layout/`).
- `src/stores/` — Zustand stores (`authStore`, `taskStore`, `projectStore`). Server state lives here; components read from stores, not from API calls directly.
- `src/services/` — axios API layer (`api.ts` sets baseURL + attaches Firebase ID token; `taskApi.ts`, `projectApi.ts`). All HTTP goes through these.
- `src/hooks/` — `useTasks`, `useProjects`, `useAuth`, `useWebSocket` — the glue between stores/services and components.
- `src/types/` — shared TS types mirroring backend Pydantic models (camelCase fields). Update these in lockstep with backend model changes.
- `src/styles/designSystem.ts` + `contexts/ThemeContext` — design tokens and dark/light theme.

## Conventions

- Functional components + hooks only. One responsibility per component; extract logic into hooks.
- New API call → add to a service in `src/services/`, expose via store/hook, then consume in components. Don't call axios in components.
- Firebase client config: `src/config/firebase.ts` (uses `VITE_*` env vars from `.env`).
- Drag & drop: dnd-kit (`components/kanban/`). Dates: date-fns. Icons: lucide-react.
- Task/priority/status string unions must match backend literals exactly (`todo | in_progress | done | archived`, `low | medium | high | urgent`).
