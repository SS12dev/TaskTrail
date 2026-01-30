# API Reference (TaskTrail)

**Last Updated:** January 29, 2026

## Auth
### Verify Token
- **POST** `/api/v1/auth/verify`
- **Headers:** `Authorization: Bearer <token>`
- **Response:** `{ uid, email, name, photoURL }`

## Tasks
### List Tasks
- **GET** `/api/v1/tasks`
- **Query:** `status`, `priority`, `project_id`, `include_completed`

### Create Task
- **POST** `/api/v1/tasks`
- **Body:**
```json
{
  "title": "string",
  "description": "string",
  "priority": "low|medium|high|urgent",
  "dueDate": "YYYY-MM-DD or ISO",
  "tags": ["string"],
  "projectId": "string|null"
}
```

### Update Task
- **PUT** `/api/v1/tasks/{task_id}`
- **Body:** (partial)
```json
{ "title": "...", "status": "todo|in_progress|done|archived" }
```

### Delete Task
- **DELETE** `/api/v1/tasks/{task_id}`

## Projects
### List Projects
- **GET** `/api/v1/projects`

### Create Project
- **POST** `/api/v1/projects`
- **Body:**
```json
{ "name": "string", "description": "string", "color": "blue" }
```

### Update Project
- **PUT** `/api/v1/projects/{project_id}`

### Delete Project
- **DELETE** `/api/v1/projects/{project_id}`

## Agent & Conversations
### Create Conversation
- **POST** `/api/v1/agent/conversations`
- **Body:** `{ "title": "optional", "initial_message": "optional" }`

### List Conversations
- **GET** `/api/v1/agent/conversations?archived=false`

### Get Conversation
- **GET** `/api/v1/agent/conversations/{conversation_id}`

### Update Conversation
- **PUT** `/api/v1/agent/conversations/{conversation_id}`

### Delete Conversation
- **DELETE** `/api/v1/agent/conversations/{conversation_id}?permanent=false`

### Chat
- **POST** `/api/v1/agent/chat`
- **Body:**
```json
{ "message": "string", "conversation_id": "optional" }
```
- **Response:**
```json
{ "type": "response", "message": "...", "task": null, "tasks": null }
```

## Memory (Optional)
### Stats
- **GET** `/api/v1/memory/stats`

### Compact
- **POST** `/api/v1/memory/compact`

### Export
- **POST** `/api/v1/memory/export`

---

## Admin (Authenticated Admins Only)

All admin endpoints require `Authorization: Bearer <admin_token>` header.

### User Management

#### List Users
- **GET** `/api/v1/admin/users`
- **Query Params:**
  - `page` (default: 1)
  - `page_size` (default: 20)
  - `status` - `active`, `suspended`, `deleted`
  - `tier` - `free`, `pro`, `enterprise`
  - `search` - Search by email
- **Permissions:** `view_users`

#### Get User Details
- **GET** `/api/v1/admin/users/{user_id}`
- **Permissions:** `view_users`
- **Response:**
```json
{
  "uid": "string",
  "email": "string",
  "displayName": "string",
  "tier": "free",
  "status": "active",
  "createdAt": "ISO date",
  "lastActive": "ISO date",
  "stats": {
    "totalTasks": 0,
    "totalProjects": 0,
    "totalConversations": 0,
    "totalTokensUsed": 0,
    "totalCost": 0.0
  }
}
```

#### Update User
- **PATCH** `/api/v1/admin/users/{user_id}`
- **Permissions:** `edit_users`
- **Body:**
```json
{
  "tier": "pro",
  "status": "suspended",
  "notes": "Suspended for policy violation"
}
```

#### Delete User
- **DELETE** `/api/v1/admin/users/{user_id}`
- **Permissions:** `delete_users` (super_admin only)

#### Get User Token Usage
- **GET** `/api/v1/admin/users/{user_id}/usage`
- **Query Params:**
  - `days` (default: 30)
- **Permissions:** `view_users`
- **Response:**
```json
{
  "userId": "string",
  "period": "30d",
  "totalTokens": 15000,
  "totalCost": 0.56,
  "dailyUsage": [
    {
      "date": "2026-01-30",
      "tokens": 500,
      "requests": 12,
      "cost": 0.02,
      "models": {
        "gpt-4o-mini": 500
      }
    }
  ]
}
```

### Analytics

#### System Overview
- **GET** `/api/v1/admin/analytics/overview`
- **Permissions:** `view_analytics`
- **Response:**
```json
{
  "totalUsers": 1250,
  "activeUsers7d": 340,
  "activeUsers30d": 890,
  "totalTasks": 15420,
  "totalProjects": 2310,
  "totalTokensThisMonth": 2450000,
  "totalCostThisMonth": 91.87,
  "usersByTier": {
    "free": 1100,
    "pro": 140,
    "enterprise": 10
  }
}
```

#### Top Users by Usage
- **GET** `/api/v1/admin/analytics/top-users`
- **Query Params:**
  - `metric` - `tokens`, `cost`, `requests` (default: tokens)
  - `period` - `7d`, `30d`, `90d` (default: 30d)
  - `limit` (default: 10)
- **Permissions:** `view_analytics`

### Configuration

#### Get System Configuration
- **GET** `/api/v1/admin/config`
- **Permissions:** `manage_api_keys`
- **Response:**
```json
{
  "openai": {
    "apiKey": "sk-...xyz",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "maxTokens": 1500
  },
  "tiers": {
    "free": {
      "monthlyTokenLimit": 100000,
      "features": ["basic_tasks", "basic_projects"],
      "price": 0
    },
    "pro": {
      "monthlyTokenLimit": 1000000,
      "features": ["basic_tasks", "basic_projects", "advanced_ai", "priority_support"],
      "price": 19.99
    }
  },
  "features": {
    "vectorMemory": true,
    "a2aEnabled": false,
    "maintenanceMode": false
  }
}
```

#### Update Configuration
- **PATCH** `/api/v1/admin/config`
- **Permissions:** `manage_api_keys` (super_admin only)
- **Body:**
```json
{
  "openai": {
    "model": "gpt-4o",
    "temperature": 0.8
  },
  "features": {
    "maintenanceMode": true
  }
}
```

### Audit Logs

#### List Audit Logs
- **GET** `/api/v1/admin/audit-logs`
- **Query Params:**
  - `page` (default: 1)
  - `page_size` (default: 50)
  - `action` - Filter by action type
  - `resource_type` - Filter by resource
  - `admin_id` - Filter by admin
  - `start_date`, `end_date` - Date range
- **Permissions:** `view_audit_logs`
- **Response:**
```json
{
  "logs": [
    {
      "id": "string",
      "timestamp": "ISO date",
      "adminId": "string",
      "adminEmail": "string",
      "action": "user_suspended",
      "resourceType": "user",
      "resourceId": "user123",
      "changes": {
        "status": {
          "old": "active",
          "new": "suspended"
        }
      },
      "ipAddress": "192.168.1.1"
    }
  ],
  "total": 150,
  "page": 1,
  "pageSize": 50
}
```
