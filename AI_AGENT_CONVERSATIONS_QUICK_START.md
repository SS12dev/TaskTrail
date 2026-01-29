# AI Agent Conversations - Quick Start Guide

## For Users

### Starting Your First Conversation

1. **Navigate to AI Agent**
   - Click "AI Agent" in the sidebar
   - You'll see the conversation interface

2. **Create a New Conversation**
   - Click the **"New Chat"** button in the left sidebar
   - Start typing your message

3. **First Message Options**
   - Type naturally: "Create a task to buy groceries by tomorrow"
   - Use suggested prompts shown in the interface
   - Conversation creates automatically when you send

### Managing Conversations

**View All Conversations**
- They appear in the left sidebar sorted by most recent first
- Each shows:
  - Conversation title (auto-generated from first message)
  - Number of messages
  - Last updated time

**Continue a Conversation**
- Click any conversation in the sidebar
- All previous messages appear
- New messages will use full conversation context
- Agent remembers everything from this conversation

**Archive a Conversation**
- Hover over conversation in sidebar
- Click the archive icon
- Hidden from active list, but not deleted
- Recover from "Show Archived" toggle

**Delete a Conversation**
- Hover over conversation in sidebar
- Click the trash icon
- Confirm permanent deletion
- Cannot be recovered

### Best Practices

✅ **Do This:**
- Keep related tasks in the same conversation
- Reference previous items: "Create a task for step 2"
- Build on prior context: "Like the first task, but with..."

❌ **Avoid This:**
- Switching conversations for related questions
- Starting new conversation when continuing same project
- Assuming agent remembers from other conversations

---

## For Developers

### Backend Implementation

#### 1. Conversation Model
```python
# app/models/conversation.py
from typing import TypedDict

class Conversation(TypedDict):
    id: str                  # UUID
    user_id: str            # Firebase UID
    title: str              # Auto-generated or user-set
    messages: List          # Chat history
    created_at: datetime
    updated_at: datetime
    archived: bool
    metadata: dict          # agents_used, tasks_created, etc.
```

#### 2. Conversation Service
```python
# app/services/conversation_service.py
service = ConversationService(user_id)

# Create new conversation
conv_id = service.create_conversation(title="My Project")

# Load conversation
conv = service.get_conversation(conv_id)

# Add messages
service.add_message(conv_id, "user", "Create a task")
service.add_message(conv_id, "assistant", "Done!")

# Get context for agent
context = service.get_conversation_context(conv_id, max_messages=10)

# List conversations
convs = service.list_conversations(limit=50, archived=False)

# Archive/Delete
service.archive_conversation(conv_id)
service.delete_conversation(conv_id)
```

#### 3. API Endpoints

```
# Create conversation
POST /api/v1/agent/conversations
Response: { id, title, message_count, created_at }

# List conversations
GET /api/v1/agent/conversations?limit=50&archived=false
Response: List[{ id, title, message_count, updated_at, archived }]

# Get full conversation
GET /api/v1/agent/conversations/{conversation_id}
Response: { id, title, messages[], created_at, updated_at, archived, metadata }

# Update title
PUT /api/v1/agent/conversations/{conversation_id}?title=new_title
Response: { success, message }

# Archive/Delete
DELETE /api/v1/agent/conversations/{conversation_id}?permanent=false
Response: { success, message }

# Chat (updated)
POST /api/v1/agent/chat
Body: { message: string, conversation_id?: string }
Response: { type, message, conversation_id, task?, tasks? }
```

#### 4. Context-Aware Agent
```python
# app/services/agent_service.py
async def process_text_message(
    self,
    user_id: str,
    message: str,
    context: Optional[str] = None  # Conversation history
) -> Dict:
    # If context provided, agent receives full conversation
    # Enables multi-turn awareness and follow-up understanding
```

### Frontend Implementation

#### 1. Conversation Hook
```typescript
// hooks/useConversations.ts
const {
    currentConversation,              // Current conv data
    isLoading, error,                 // States
    createConversation,               // () -> Promise<id>
    loadConversation,                 // (id) -> Promise
    sendMessage,                      // (msg) -> Promise<response>
    updateConversationTitle,          // (id, title) -> Promise
    archiveConversation,              // (id) -> Promise
    deleteConversation                // (id) -> Promise
} = useConversations();
```

#### 2. Conversation List Component
```typescript
// components/agent/ConversationList.tsx
<ConversationList
    onSelectConversation={(convId) => loadConversation(convId)}
    currentConversationId={current?.id}
/>
```

#### 3. Agent Page Integration
```typescript
// pages/AgentPage.tsx
const AgentPage = () => {
    const { currentConversation, sendMessage, ... } = useConversations();
    
    // On mount/load conv: render messages from conversation
    // On send message: call sendMessage() which:
    //   - Creates conv if needed
    //   - Sends with conversation_id
    //   - Backend loads context
    //   - Updates local state
};
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (React)                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  AgentPage (Main Chat Interface)                │  │
│  │  - displays messages                            │  │
│  │  - manages input                                │  │
│  │  - uses useConversations hook                   │  │
│  └─────────────────────────────────────────────────┘  │
│               │            │                            │
│         ┌─────┘            └─────┐                      │
│         ▼                        ▼                       │
│  ┌─────────────────┐    ┌──────────────────────┐       │
│  │ ConversationList│    │ useConversations Hook│       │
│  │ (Sidebar)       │    │ (State Mgmt)         │       │
│  └─────────────────┘    └──────────────────────┘       │
│                              │                          │
│                         Calls API                       │
│                              │                          │
└──────────────────────────────┼──────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
┌───────────────────▼──┐      ┌──────────▼────────────────┐
│  BACKEND (FastAPI)   │      │ STORAGE                   │
│                      │      │                           │
│ ┌──────────────────┐ │      │ ┌────────────────────┐   │
│ │ Agent Routes     │ │      │ │ Firebase Firestore │   │
│ │ - /chat          │ │      │ │ (Persistent)       │   │
│ │ - /conversations │◄──────┤ │ users/{uid}/convs/ │   │
│ └──────────────────┘ │      │ └────────────────────┘   │
│                      │      │                           │
│ ┌──────────────────┐ │      │ ┌────────────────────┐   │
│ │ Conversation     │ │      │ │ Redis Cache        │   │
│ │ Service          │◄──────┤ │ (1 hour TTL)       │   │
│ │ - CRUD ops       │ │      │ │ conv:{uid}:{id}    │   │
│ │ - Context mgmt   │ │      │ └────────────────────┘   │
│ └──────────────────┘ │      │                           │
│                      │      │                           │
│ ┌──────────────────┐ │      │                           │
│ │ Agent Service    │ │      │                           │
│ │ - process_message│ │      │                           │
│ │   + context param│ │      │                           │
│ └──────────────────┘ │      │                           │
└──────────────────────┘      └──────────────────────────┘
```

### Adding to Existing Project

**Step 1: Backend Files**
```
✅ Copy:
- app/models/conversation.py
- app/services/conversation_service.py

✅ Update:
- app/routes/agent.py (add new endpoints)
- app/services/agent_service.py (add context param)
```

**Step 2: Frontend Files**
```
✅ Create:
- components/agent/ConversationList.tsx
- hooks/useConversations.ts

✅ Replace:
- pages/AgentPage.tsx (with conversation support)
```

**Step 3: Database Setup**
```
✅ Firestore Collection:
users/{uid}/conversations/{conversation_id}

✅ Fields (auto-created by ConversationService):
- id, title, messages, created_at, updated_at, archived, metadata
```

**Step 4: Test**
```bash
# Backend
python run_dev.py

# Frontend  
npm run dev

# Navigate to /agent
# Create conversation, send messages
# Check Firestore for stored data
```

---

## API Testing Examples

### Using cURL

```bash
# Create conversation
curl -X POST http://localhost:8000/api/v1/agent/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# List conversations
curl -X GET "http://localhost:8000/api/v1/agent/conversations?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Send message
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a task",
    "conversation_id": "uuid-here"
  }'

# Get conversation
curl -X GET http://localhost:8000/api/v1/agent/conversations/{id} \
  -H "Authorization: Bearer $TOKEN"
```

### Using Python

```python
import requests

headers = {"Authorization": f"Bearer {token}"}

# Create
resp = requests.post(
    "http://localhost:8000/api/v1/agent/conversations",
    headers=headers
)
conv_id = resp.json()["id"]

# Chat
resp = requests.post(
    "http://localhost:8000/api/v1/agent/chat",
    headers=headers,
    json={
        "message": "Break down the project",
        "conversation_id": conv_id
    }
)
print(resp.json()["message"])
```

---

## Monitoring & Debugging

### Check Firestore Data
```
1. Firebase Console → Firestore
2. Navigate: Database → users → {uid} → conversations
3. Each conversation_id has:
   - Title, messages[], created_at, updated_at, archived, metadata
```

### Check Redis Cache
```bash
# Connect to Redis
redis-cli

# Check cached conversations
KEYS conv:*

# Get specific conversation
GET conv:{user_id}:{conversation_id}

# Check TTL
TTL conv:{user_id}:{conversation_id}
```

### View Backend Logs
```bash
# Running backend shows:
INFO: ConversationService: Created conversation {id}
INFO: Added user message to conversation {id}
DEBUG: Retrieved conversation {id} from Redis
INFO: Updated metadata for conversation {id}
```

### Frontend Console
```javascript
// Check current conversation state
console.log(currentConversation);

// Check error messages
console.log(error);

// Monitor API calls (Network tab in DevTools)
// Should see POST /api/v1/agent/chat calls
```

---

## Performance Tips

### For Large Conversations
```typescript
// Paginate messages (future enhancement)
const recentMessages = messages.slice(-50); // Last 50 messages
const olderMessages = messages.slice(0, -50); // Before that

// Limit context window
const context = getConversationContext(id, max_messages: 15);
```

### Caching Strategy
```typescript
// Keep conversations in React state for current session
const [conversationCache, setConversationCache] = useState({});

// Avoid re-fetching same conversation
if (conversationCache[id]) {
    return conversationCache[id];
}
```

### Database Indexing
```firestore
# Firestore automatically indexes:
- users/{uid}/conversations ordered by updated_at DESC
- users/{uid}/conversations filtered by archived

# No additional setup needed
```

---

## Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| Conversation not saving | Firestore permissions | Check Firebase rules for `users/{uid}/conversations` |
| Slow context loading | Large message count | Reduce `max_messages` parameter |
| Agent losing context | Context not passed | Verify `context` param in `process_text_message` |
| Old conversation doesn't load | Cache expired | Clear Redis cache, reload from Firestore |
| New user has no convs | First user setup | Create first conversation manually or UI |
| Messages out of order | Timestamp issues | Verify server time sync |

---

## Next Steps

1. **Test Thoroughly**: Run through user flows in both browsers
2. **Monitor Firestore**: Watch quota usage during testing
3. **Gather Feedback**: Ask users about context awareness
4. **Optimize**: Adjust `max_messages` based on performance
5. **Document**: Add to user help documentation
6. **Release**: Deploy to production with monitoring

---

## Summary

✅ **Users**: Get intelligent, context-aware conversations
✅ **Developers**: Clean API with persistent storage
✅ **Scalability**: Handles unlimited conversations per user
✅ **Performance**: Redis caching + Firestore persistence
✅ **Reliability**: Graceful error handling throughout

**The AI Agent is now conversation-smart!** 🚀
