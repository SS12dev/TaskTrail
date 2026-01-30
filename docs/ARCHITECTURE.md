# TaskTrail System Architecture

Visual overview of the complete TaskTrail system architecture.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USERS                                       │
│                                                                          │
│  ┌──────────────┐         ┌──────────────┐        ┌──────────────┐    │
│  │  End Users   │         │   Admins     │        │   Support    │    │
│  │  (Frontend)  │         │  (Admin UI)  │        │    Team      │    │
│  └──────┬───────┘         └──────┬───────┘        └──────┬───────┘    │
│         │                        │                       │             │
└─────────┼────────────────────────┼───────────────────────┼─────────────┘
          │                        │                       │
          │                        │                       │
┌─────────┼────────────────────────┼───────────────────────┼─────────────┐
│         │        DOCKER COMPOSE  │                       │             │
│         ▼                        ▼                       ▼             │
│  ┌──────────────┐         ┌──────────────┐        ┌──────────────┐   │
│  │   Frontend   │         │    Admin     │        │    Nginx     │   │
│  │    :5173     │         │  Frontend    │        │  (Optional)  │   │
│  │   (Vite)     │         │    :3001     │        │   :80/:443   │   │
│  └──────┬───────┘         └──────┬───────┘        └──────┬───────┘   │
│         │                        │                       │             │
│         └────────────────────────┴───────────────────────┘             │
│                                   │                                    │
│                            ┌──────▼────────┐                           │
│                            │  Backend API  │                           │
│                            │     :8000     │                           │
│                            │   (FastAPI)   │                           │
│                            └──────┬────────┘                           │
│                                   │                                    │
│                      ┌────────────┼────────────┐                      │
│                      ▼            ▼            ▼                      │
│              ┌────────────┐ ┌─────────┐ ┌──────────────┐             │
│              │   Redis    │ │ Memory  │ │ Multi-Agent  │             │
│              │   :6379    │ │ Service │ │    System    │             │
│              │  (Cache)   │ │         │ │  (LangGraph) │             │
│              └────────────┘ └─────────┘ └──────┬───────┘             │
│                                                 │                      │
└─────────────────────────────────────────────────┼──────────────────────┘
                                                  │
┌─────────────────────────────────────────────────┼──────────────────────┐
│                         EXTERNAL SERVICES       │                      │
│                                                 │                      │
│  ┌──────────────┐         ┌──────────────┐    ▼                      │
│  │   Firebase   │         │   OpenAI     │  ┌──────────────┐         │
│  │              │         │     API      │  │    Token     │         │
│  │ • Auth       │         │              │  │   Tracker    │         │
│  │ • Firestore  │◄────────┤ • GPT-4o     │  │   Service    │         │
│  │ • Storage    │         │ • GPT-4o-mini│  └──────────────┘         │
│  └──────────────┘         └──────────────┘                            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Service Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    API Routes                               │    │
│  │                                                             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │  Tasks   │  │ Projects │  │  Agent   │  │  Admin   │  │    │
│  │  │  /tasks  │  │/projects │  │  /agent  │  │  /admin  │  │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │    │
│  │       │             │             │             │         │    │
│  └───────┼─────────────┼─────────────┼─────────────┼─────────┘    │
│          │             │             │             │               │
│  ┌───────┼─────────────┼─────────────┼─────────────┼─────────┐    │
│  │       │  Middleware │             │             │         │    │
│  │       │             │             │             │         │    │
│  │  ┌────▼─────┐  ┌───▼──────┐  ┌───▼──────┐  ┌───▼──────┐ │    │
│  │  │   Auth   │  │  CORS    │  │  Error   │  │  Rate    │ │    │
│  │  │  Check   │  │  Handler │  │  Handler │  │  Limit   │ │    │
│  │  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘ │    │
│  │       │                                                   │    │
│  └───────┼───────────────────────────────────────────────────┘    │
│          │                                                         │
│  ┌───────▼─────────────────────────────────────────────────────┐  │
│  │                    Services Layer                           │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │
│  │  │   Task      │  │   Agent     │  │   Token          │  │  │
│  │  │  Service    │  │  Service    │  │   Tracker        │  │  │
│  │  └─────────────┘  └──────┬──────┘  └──────────────────┘  │  │
│  │                          │                                │  │
│  │  ┌─────────────┐  ┌──────▼──────┐  ┌──────────────────┐  │  │
│  │  │  Project    │  │   Multi-    │  │  Conversation    │  │  │
│  │  │  Service    │  │   Agent     │  │    Memory        │  │  │
│  │  └─────────────┘  │   System    │  └──────────────────┘  │  │
│  │                   │ (LangGraph) │                        │  │
│  │                   └──────┬──────┘                        │  │
│  └──────────────────────────┼───────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Multi-Agent System                          │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │Supervisor│  │  Planner │  │ Executor │  │  Query  │ │  │
│  │  │  Agent   │─▶│  Agent   │─▶│  Agent   │  │  Agent  │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │  │
│  │       │                                                  │  │
│  │       └──────────────────┐                              │  │
│  │                          ▼                              │  │
│  │                  ┌──────────────┐                       │  │
│  │                  │Conversation  │                       │  │
│  │                  │   Agent      │                       │  │
│  │                  └──────────────┘                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. User Task Creation via AI

```
┌──────┐   1. "Create task"    ┌──────────┐
│ User ├──────────────────────▶│ Frontend │
└──────┘                       └────┬─────┘
                                    │
                         2. POST /agent/chat
                                    │
                               ┌────▼─────┐
                               │ Backend  │
                               │   API    │
                               └────┬─────┘
                                    │
                         3. Process message
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        │     Multi-Agent System    │                           │
        │                           │                           │
        │  ┌────────────────────────▼─────────────────────┐    │
        │  │ Supervisor Agent                             │    │
        │  │ • Analyzes intent                            │    │
        │  │ • Routes to: Executor Agent                  │    │
        │  └────────────────────┬─────────────────────────┘    │
        │                       │                               │
        │  ┌────────────────────▼─────────────────────────┐    │
        │  │ Executor Agent                               │    │
        │  │ • Calls OpenAI GPT-4o-mini                   │────┐
        │  │ • Token usage tracked automatically          │    │
        │  │ • Creates task via TaskService               │    │
        │  └────────────────────┬─────────────────────────┘    │
        │                       │                               │
        └───────────────────────┼───────────────────────────────┘
                                │
                    4. Save to Firestore
                                │
                         ┌──────▼─────┐
                         │  Firebase  │
                         │ Firestore  │
                         └──────┬─────┘
                                │
                    5. Return task + response
                                │
                         ┌──────▼─────┐
                         │ Frontend   │
                         │  Updates   │
                         └────────────┘
```

### 2. Token Tracking Flow

```
┌──────────────┐   OpenAI API Call   ┌──────────────┐
│ Multi-Agent  ├────────────────────▶│   OpenAI     │
│   System     │                     │     API      │
└──────┬───────┘                     └──────┬───────┘
       │                                    │
       │                         Response with token usage
       │                                    │
       │           ┌────────────────────────┘
       │           │
       │  ┌────────▼────────────────────────────────────┐
       │  │ TokenTrackingCallback.on_llm_end()          │
       │  │ • Extract: total_tokens, model_name         │
       │  │ • Calculate cost                            │
       │  └────────┬────────────────────────────────────┘
       │           │
       │  ┌────────▼────────────────────────────────────┐
       │  │ TokenTracker.record_usage()                 │
       │  │ • user_id: from context                     │
       │  │ • tokens: from response                     │
       │  │ • model: gpt-4o-mini                        │
       │  │ • cost: auto-calculated                     │
       │  └────────┬────────────────────────────────────┘
       │           │
       │  ┌────────▼────────────────────────────────────┐
       │  │ Firestore Write                             │
       │  │ Path: users/{uid}/usage/tokens/daily/       │
       │  │       {YYYY-MM-DD}                          │
       │  │                                             │
       │  │ Data: {                                     │
       │  │   openai_tokens: 1250,                      │
       │  │   requests_count: 1,                        │
       │  │   cost_estimate: 0.046875,                  │
       │  │   models: {                                 │
       │  │     "gpt-4o-mini": 1250                     │
       │  │   }                                         │
       │  │ }                                           │
       │  └─────────────────────────────────────────────┘
       │
       └──────▶ Continue processing (non-blocking)
```

### 3. Admin User Management Flow

```
┌──────┐  1. Login (Firebase Auth)   ┌──────────────┐
│Admin ├────────────────────────────▶│ Admin Portal │
└──────┘                              └──────┬───────┘
                                             │
                            2. GET /admin/users
                                             │
                                      ┌──────▼───────┐
                                      │  Backend API │
                                      └──────┬───────┘
                                             │
                            3. Verify admin token + role
                                             │
                                ┌────────────▼────────────┐
                                │ dependencies_admin.py   │
                                │ • Check admin status    │
                                │ • Verify permissions    │
                                │ • Log audit entry       │
                                └────────────┬────────────┘
                                             │
                            4. Query Firestore users collection
                                             │
                                      ┌──────▼───────┐
                                      │   Firebase   │
                                      │  Firestore   │
                                      └──────┬───────┘
                                             │
                            5. Fetch token usage data
                                             │
                  ┌─────────────────────────┼─────────────────────────┐
                  │                         │                         │
           ┌──────▼─────────┐    ┌─────────▼────────┐    ┌──────────▼────────┐
           │ User Profile   │    │  Token Usage     │    │  Activity Data    │
           │ Collection     │    │  Subcollection   │    │  (tasks/projects) │
           └──────┬─────────┘    └─────────┬────────┘    └──────────┬────────┘
                  │                         │                         │
                  └─────────────────────────┴─────────────────────────┘
                                            │
                            6. Aggregate and format response
                                            │
                                     ┌──────▼───────┐
                                     │ Admin Portal │
                                     │  • User list │
                                     │  • Stats     │
                                     │  • Actions   │
                                     └──────────────┘
```

---

## Database Schema (Firestore)

```
Firestore Root
│
├── users/
│   └── {userId}/
│       ├── profile                    (document)
│       │   ├── email
│       │   ├── displayName
│       │   ├── createdAt
│       │   └── lastActive
│       │
│       ├── tasks/                     (subcollection)
│       │   └── {taskId}/
│       │       ├── title
│       │       ├── status
│       │       ├── priority
│       │       └── dueDate
│       │
│       ├── projects/                  (subcollection)
│       │   └── {projectId}/
│       │       ├── name
│       │       └── description
│       │
│       ├── conversations/             (subcollection)
│       │   └── {conversationId}/
│       │       ├── messages[]
│       │       └── metadata
│       │
│       └── usage/
│           └── tokens/
│               └── daily/
│                   └── {YYYY-MM-DD}/  (document)
│                       ├── openai_tokens
│                       ├── requests_count
│                       ├── cost_estimate
│                       └── models {}
│
├── admins/
│   └── {adminId}/                     (document)
│       ├── email
│       ├── role: super_admin|admin|support
│       ├── permissions[]
│       ├── createdAt
│       ├── lastLogin
│       └── status: active|suspended
│
├── system_config/                     (collection)
│   └── default/                       (document)
│       ├── openai
│       │   ├── apiKey (encrypted)
│       │   ├── model
│       │   └── temperature
│       ├── tiers
│       │   ├── free {}
│       │   ├── pro {}
│       │   └── enterprise {}
│       └── features
│           ├── vectorMemory
│           ├── a2aEnabled
│           └── maintenanceMode
│
└── admin_audit_log/                   (collection)
    └── {logId}/                       (document)
        ├── timestamp
        ├── adminId
        ├── adminEmail
        ├── action
        ├── resourceType
        ├── resourceId
        ├── changes {}
        └── ipAddress
```

---

## Security Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        Security Layers                             │
│                                                                    │
│  1. Network Layer                                                 │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │ • Firewall (ports 80, 443, 22 only)                      │ │
│     │ • DDoS protection                                        │ │
│     │ • Rate limiting (IP-based)                               │ │
│     └──────────────────────────────────────────────────────────┘ │
│                                                                    │
│  2. Application Layer                                             │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │ • CORS (allowed origins only)                            │ │
│     │ • Request validation (Pydantic)                          │ │
│     │ • Rate limiting (user-based)                             │ │
│     │ • Error sanitization                                     │ │
│     └──────────────────────────────────────────────────────────┘ │
│                                                                    │
│  3. Authentication Layer                                          │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │ • Firebase Auth (JWT tokens)                             │ │
│     │ • Token expiration (1 hour)                              │ │
│     │ • Refresh token rotation                                 │ │
│     │ • MFA support (optional)                                 │ │
│     └──────────────────────────────────────────────────────────┘ │
│                                                                    │
│  4. Authorization Layer                                           │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │ • Role-Based Access Control (RBAC)                       │ │
│     │   - super_admin: Full access                            │ │
│     │   - admin: Most operations                              │ │
│     │   - support: Read-only + limited actions                │ │
│     │ • Permission checks on every endpoint                    │ │
│     │ • Resource ownership validation                          │ │
│     └──────────────────────────────────────────────────────────┘ │
│                                                                    │
│  5. Data Layer                                                    │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │ • Firestore security rules                               │ │
│     │ • Encrypted API keys in database                         │ │
│     │ • Secrets in environment variables                       │ │
│     │ • No sensitive data in logs                              │ │
│     └──────────────────────────────────────────────────────────┘ │
│                                                                    │
│  6. Audit Layer                                                   │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │ • All admin actions logged                               │ │
│     │ • Immutable audit trail                                  │ │
│     │ • IP address tracking                                    │ │
│     │ • Change history maintained                              │ │
│     └──────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture (Production)

```
                        ┌─────────────────┐
                        │   CloudFlare    │
                        │   DNS + CDN     │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼──────┐          ┌──────▼───────┐
            │  tasktrail   │          │    admin     │
            │ .example.com │          │.example.com  │
            └───────┬──────┘          └──────┬───────┘
                    │                        │
┌───────────────────┼────────────────────────┼──────────────────────┐
│                   │    Load Balancer       │                      │
│            ┌──────▼────────────────────────▼──────┐               │
│            │         Nginx Reverse Proxy          │               │
│            │  • SSL Termination                   │               │
│            │  • Rate Limiting                     │               │
│            │  • Static File Serving               │               │
│            └──────┬────────────────────────┬──────┘               │
│                   │                        │                      │
│        ┌──────────┴──────────┐  ┌─────────┴──────────┐           │
│        │                     │  │                    │           │
│  ┌─────▼─────┐        ┌─────▼─────┐          ┌─────▼─────┐     │
│  │ Frontend  │        │  Backend  │          │   Admin   │     │
│  │ Container │        │    API    │          │ Container │     │
│  │  (React)  │        │ Container │          │  (React)  │     │
│  └───────────┘        │ (FastAPI) │          └───────────┘     │
│                       └─────┬─────┘                             │
│                             │                                   │
│                  ┌──────────┼──────────┐                        │
│                  │          │          │                        │
│           ┌──────▼───┐ ┌───▼────┐ ┌───▼────────┐               │
│           │  Redis   │ │ Redis  │ │   Redis    │               │
│           │ (Cache)  │ │(Vector)│ │ (Sessions) │               │
│           └──────────┘ └────────┘ └────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼─────┐            ┌─────▼──────┐
         │  Firebase  │            │   OpenAI   │
         │            │            │    API     │
         │ • Auth     │            │            │
         │ • Firestore│            │ • GPT-4o   │
         │ • Storage  │            │ • Embed    │
         └────────────┘            └────────────┘
```

---

*Last Updated: January 30, 2026*
