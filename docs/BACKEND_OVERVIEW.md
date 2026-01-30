# Backend Overview (TaskTrail)

**Last Updated:** January 29, 2026

## Purpose
TaskTrail backend is a FastAPI service that powers task/project management and the AI Agent. It handles authentication, persistence, and orchestration for AI workflows.

## Core Components

### API Layer (FastAPI)
- **Routes:** auth, tasks, projects, agent, memory, dev
- **Auth:** Firebase ID tokens (Bearer)
- **Base URL:** http://127.0.0.1:8000

### Services
- **TaskService:** CRUD for tasks, smart inbox queries
- **ProjectService:** CRUD for projects, project task aggregation
- **ConversationService:** Conversation persistence + Redis caching
- **AgentService:** LangGraph orchestration + context injection
- **UserPreferences:** User timezone/locale support
- **VectorMemory (optional):** Semantic memory search (Redis)

### Agents (LangGraph)
- **SupervisorAgent:** Routes to specialist agents
- **ConversationAgent:** General Q&A
- **PlannerAgent:** Breaks goals into tasks
- **ExecutorAgent:** Creates/updates tasks
- **QueryAgent:** Lists/filters tasks

## Data Persistence (Firestore)
```
users/{userId}/conversations/{conversationId}
users/{userId}/projects/{projectId}
tasks/{taskId}  (root collection with userId field)
```

## Caching (Redis)
- Conversations cached for 1 hour
- Key: `conv:{userId}:{conversationId}`

## Key Design Decisions
- User isolation via `userId` field and subcollections
- Avoid Firestore composite index requirements by in-memory filtering
- Server timestamps for top-level fields; message timestamps use `datetime.utcnow()`

## Operational Notes
- APScheduler is optional (compaction scheduler)
- Redis is optional (conversation cache, vector memory)
- System remains functional without optional dependencies
