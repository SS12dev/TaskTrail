# Backend Summary for Frontend Developers

**Last Updated:** January 29, 2026

## Authentication
All API requests require a Firebase ID token in the Authorization header:
```
Authorization: Bearer <firebase_id_token>
```

## Base URLs
- **API:** http://127.0.0.1:8000
- **Docs (Swagger):** http://127.0.0.1:8000/docs

## Core APIs Used by Frontend

### Tasks
- **List tasks**
  - `GET /api/v1/tasks`
  - Query params: `status`, `priority`, `project_id`, `include_completed`
- **Create task**
  - `POST /api/v1/tasks`
- **Update task**
  - `PUT /api/v1/tasks/{task_id}`
- **Delete task**
  - `DELETE /api/v1/tasks/{task_id}`

### Projects
- **List projects**
  - `GET /api/v1/projects`
- **Create project**
  - `POST /api/v1/projects`
- **Update project**
  - `PUT /api/v1/projects/{project_id}`
- **Delete project**
  - `DELETE /api/v1/projects/{project_id}`

### AI Agent + Conversations
- **Create conversation**
  - `POST /api/v1/agent/conversations`
- **List conversations**
  - `GET /api/v1/agent/conversations?archived=false`
- **Get conversation**
  - `GET /api/v1/agent/conversations/{conversation_id}`
- **Send chat message**
  - `POST /api/v1/agent/chat`
  - Body:
    ```json
    { "message": "...", "conversation_id": "optional" }
    ```
- **Delete conversation**
  - `DELETE /api/v1/agent/conversations/{conversation_id}?permanent=false`

## Response Shapes (Key)

### Task (example)
```json
{
  "id": "task-id",
  "title": "Design Homepage Mockup",
  "description": "...",
  "status": "todo",
  "priority": "high",
  "dueDate": "2026-02-05T00:00:00",
  "projectId": null
}
```

### Conversation List Item
```json
{
  "id": "conv-id",
  "title": "What should I focus on today?",
  "message_count": 6,
  "updated_at": "2026-01-29T19:28:00",
  "archived": false
}
```

### Agent Chat Response
```json
{
  "type": "response",
  "message": "...assistant reply...",
  "task": null,
  "tasks": null
}
```

## Important UI Notes
- Conversation titles are auto-generated from the first user message.
- Conversations are cached, but updates invalidate cache automatically.
- Tasks are stored in a root collection with `userId` field for filtering.

## Common Errors
- **401/403:** Invalid or missing Firebase token
- **400:** Firestore index requirement (handled by in-memory filtering)
- **500:** OpenAI API or internal error
