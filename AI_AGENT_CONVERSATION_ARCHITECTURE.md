# AI Agent Conversation Architecture

## Overview

The TaskTrail AI Agent now features **conversation-by-conversation** tracking with persistent storage and context awareness. Each conversation is uniquely identified, maintains its own message history, and allows for long-term context understanding.

---

## Architecture

### Storage Strategy

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (React Component State)                             │
│ - Current conversation messages (for instant display)        │
│ - Active conversation ID                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌─────────────┐      ┌──────────────┐
   │    Redis    │      │ Firebase     │
   │ (1 hour TTL)│      │ (Long-term)  │
   │ Fast Cache  │      │ Persistent   │
   └─────────────┘      └──────────────┘
```

### Backend Services

#### 1. **ConversationService** (`conversation_service.py`)
Manages all conversation operations:

```python
class ConversationService:
    # Core methods:
    - create_conversation(title) -> conversation_id
    - get_conversation(id) -> Conversation (all messages)
    - list_conversations(limit, archived) -> List[Conversation]
    - add_message(id, role, content, metadata)
    - get_conversation_context(id, max_messages) -> str
    - update_conversation_metadata(id, updates)
    - archive_conversation(id)
    - delete_conversation(id)
```

**Storage location**: `users/{uid}/conversations/{conversation_id}`

```firestore
{
  "id": "uuid-1234",
  "user_id": "firebase-uid",
  "title": "Project Planning Discussion",
  "messages": [
    {
      "role": "user",
      "content": "Break down the project",
      "timestamp": "2026-01-29T...",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "Sure! Here's how I'd break it down...",
      "timestamp": "2026-01-29T...",
      "metadata": {"type": "response"}
    }
  ],
  "created_at": "2026-01-29T...",
  "updated_at": "2026-01-29T...",
  "archived": false,
  "metadata": {
    "message_count": 2,
    "agents_used": ["planner"],
    "tasks_created": ["task-id-1", "task-id-2"]
  }
}
```

#### 2. **Agent Routes** (`routes/agent.py`)

**Conversation Management Endpoints:**

```
POST   /api/v1/agent/conversations
       Create new conversation
       Response: { id, title, message_count, created_at }

GET    /api/v1/agent/conversations
       List user's conversations
       Params: limit=50, archived=false
       Response: List[ConversationListItem]

GET    /api/v1/agent/conversations/{conversation_id}
       Get full conversation with all messages
       Response: ConversationDetail

PUT    /api/v1/agent/conversations/{conversation_id}
       Update conversation title
       Params: title=new_title
       Response: { success, message }

DELETE /api/v1/agent/conversations/{conversation_id}
       Archive or permanently delete
       Params: permanent=false (archive) | true (delete)
       Response: { success, message }
```

**Chat Endpoint (Updated):**

```
POST   /api/v1/agent/chat
       Send message to agent within a conversation
       Body: {
         "message": "user message",
         "conversation_id": "optional-uuid" (auto-creates if missing)
       }
       Response: {
         "type": "response",
         "message": "agent response",
         "conversation_id": "uuid",
         "task": null,
         "tasks": null
       }
```

#### 3. **Agent Service** (`services/agent_service.py`)

Updated `process_text_message()` to accept conversation context:

```python
async def process_text_message(
    self,
    user_id: str,
    message: str,
    context: Optional[str] = None  # NEW: conversation history
) -> Dict[str, Any]:
    # If context provided, prepend to message for agent awareness
    # Agent sees full conversation history
    # Maintains semantic understanding across multiple turns
```

**Context Format:**
```
# Conversation Context
Title: Project Planning Discussion
Messages so far: 5

## Recent Messages:

USER: Break down the website redesign project

ASSISTANT: I'll help you organize the website redesign...

USER: How long for each phase?

ASSISTANT: Based on typical timelines...
```

---

## Frontend Architecture

### Components

#### 1. **ConversationList** (`components/agent/ConversationList.tsx`)

Sidebar component displaying all conversations:

```tsx
interface ConversationListProps {
  onSelectConversation: (conversationId: string) => void;
  currentConversationId?: string;
}

Features:
- List conversations sorted by recent first
- Show message count and last updated time
- Archive/delete buttons on hover
- "New Chat" button to start fresh conversation
- Toggle between active/archived conversations
- Responsive layout (mobile-friendly sidebar toggle)
```

#### 2. **useConversations** Hook (`hooks/useConversations.ts`)

State management for conversations:

```tsx
const {
  currentConversation,    // Conversation | null
  isLoading,             // boolean
  error,                 // string | null
  createConversation,    // () -> Promise<string>
  loadConversation,      // (id: string) -> Promise<void>
  sendMessage,           // (msg: string) -> Promise<string>
  updateConversationTitle,  // (id, title) -> Promise
  archiveConversation,   // (id) -> Promise
  deleteConversation     // (id) -> Promise
} = useConversations();
```

#### 3. **AgentPage** (`pages/AgentPage.tsx`)

Updated main chat interface:

```tsx
Features:
- Conversation list sidebar (toggleable on mobile)
- Current conversation display with title & message count
- Full message history from selected conversation
- Automatic conversation creation on first message
- Quick suggestion buttons
- Context-aware responses from agent
- Graceful error handling
- Dark mode support

Layout:
┌────────────┬──────────────────────────┐
│ Sidebar    │ Chat Area                │
│ - Convs    ├──────────────────────────┤
│ - New Chat │ Header (conv title)      │
│ - Archive  ├──────────────────────────┤
│ - Delete   │ Messages                 │
│            ├──────────────────────────┤
│            │ Input + Send             │
└────────────┴──────────────────────────┘
```

---

## Data Flow

### Sending a Message

```
User Types Message
        ↓
    [Enter/Send Click]
        ↓
  Display User Message
        ↓
  Create Conv if needed
        ↓
  Call sendMessage(text)
        ↓
  POST /api/v1/agent/chat
   ├─ Include conversation_id
   ├─ Backend creates new conv if needed
   ├─ Add user message to Firestore
   └─ Load conversation context
        ↓
  Agent processes with context
        ↓
  Add assistant response
        ↓
  Update Redis cache
        ↓
  Return response to frontend
        ↓
  Display Assistant Message
        ↓
  Update local conversation state
```

### Loading Existing Conversation

```
Click Conversation in List
        ↓
  Call loadConversation(id)
        ↓
  Try Redis cache first
        ↓
  If miss, fetch from Firestore
        ↓
  Cache in Redis (1 hour TTL)
        ↓
  Set as currentConversation
        ↓
  Render all messages from history
        ↓
  Display ready for new messages
```

---

## Conversation Context Mechanism

### How Context is Passed to Agent

When sending a message in an ongoing conversation:

1. **Fetch Context**: Get last N messages from conversation history
2. **Format Context**: Convert to readable string format
3. **Prepend to Message**: Add formatted context before user's latest message
4. **Send to Agent**: Agent processes full context

**Example:**
```
Without context:
"Create a task for the first step"
→ Agent: "What's the first step?"

With context:
"# Conversation Context
Title: Website Redesign
Messages so far: 3

## Recent Messages:
USER: Break down website redesign
ASSISTANT: I suggest: Design, Development, Testing, Launch
USER: Create a task for the first step"
→ Agent: "Created 'Website Design' task for you"
```

### Benefits

✅ **Long-term Context**: Agent remembers previous decisions
✅ **Reduced Ambiguity**: References to "it", "that" are understood
✅ **Better Follow-ups**: Multi-turn conversations work naturally
✅ **Task Continuity**: Related tasks grouped in same conversation
✅ **User History**: Full audit trail of all agent interactions

---

## Database Schema

### Firestore Structure

```
firestore/
├── users/
│   ├── {uid}/
│   │   ├── conversations/ (subcollection)
│   │   │   ├── {conversation_id}/
│   │   │   │   ├── id: string (UUID)
│   │   │   │   ├── title: string
│   │   │   │   ├── messages: array<{role, content, timestamp, metadata}>
│   │   │   │   ├── created_at: timestamp
│   │   │   │   ├── updated_at: timestamp
│   │   │   │   ├── archived: boolean
│   │   │   │   └── metadata: map<string, any>
```

### Redis Structure

```
Key Format: conv:{user_id}:{conversation_id}
Value: JSON string of full conversation
TTL: 3600 seconds (1 hour)

Example:
Key: "conv:user-123:uuid-456"
Value: {"id": "uuid-456", "messages": [...], ...}
```

---

## API Response Examples

### Create Conversation
```json
POST /api/v1/agent/conversations
Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New Conversation",
  "message_count": 0,
  "created_at": "2026-01-29T17:05:00Z"
}
```

### List Conversations
```json
GET /api/v1/agent/conversations?limit=10&archived=false
Response: [
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Project Planning Discussion",
    "message_count": 12,
    "updated_at": "2026-01-29T17:05:00Z",
    "archived": false
  },
  {
    "id": "660f8400-e29b-41d4-a716-446655440001",
    "title": "Task Breakdown Session",
    "message_count": 5,
    "updated_at": "2026-01-28T14:30:00Z",
    "archived": false
  }
]
```

### Get Full Conversation
```json
GET /api/v1/agent/conversations/{conversation_id}
Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Project Planning Discussion",
  "messages": [
    {
      "role": "user",
      "content": "Break down website redesign",
      "timestamp": "2026-01-29T17:00:00Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "I suggest these phases...",
      "timestamp": "2026-01-29T17:00:30Z",
      "metadata": {"type": "response"}
    }
  ],
  "created_at": "2026-01-29T17:00:00Z",
  "updated_at": "2026-01-29T17:05:00Z",
  "archived": false,
  "metadata": {
    "message_count": 2,
    "agents_used": ["planner"],
    "tasks_created": []
  }
}
```

### Send Message
```json
POST /api/v1/agent/chat
{
  "message": "Create a task for the first step",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
Response:
{
  "type": "response",
  "message": "I've created a task 'Website Design' for you.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "task": null,
  "tasks": null
}
```

---

## Usage Examples

### Starting a New Conversation
```typescript
// User clicks "New Chat"
const conversationId = await createConversation();
// Agent page displays empty conversation ready for first message
```

### Continuing an Existing Conversation
```typescript
// User clicks conversation in list
await loadConversation(conversationId);
// All previous messages displayed
// Ready for new messages in same context
```

### Sending a Message with Context
```typescript
// User types: "Create task for first step"
// Agent already knows context: "website redesign" from earlier
const response = await sendMessage("Create task for first step");
// Agent responds using full conversation history
```

### Archiving a Conversation
```typescript
// User clicks archive button
await archiveConversation(conversationId);
// Conversation hidden from active list
// Can be recovered from archived view
// Permanent delete also available
```

---

## Performance Considerations

### Caching Strategy

| Layer | Technology | TTL | Size | Use Case |
|-------|-----------|-----|------|----------|
| Browser | React State | Session | Current Conv | Instant display |
| Cache | Redis | 1 hour | All recent | Quick retrieval |
| Persistent | Firestore | ∞ | All ever | Long-term archive |

### Message Limit Optimization

- **Display**: Load all messages for selected conversation
- **Context**: Use last 10-20 messages for agent context
- **Pagination**: Can implement pagination for very long conversations

### Query Optimization

```
Firestore Indexes:
- users/{uid}/conversations (by updated_at DESC)
- users/{uid}/conversations (by created_at DESC)
- users/{uid}/conversations (by archived)
```

---

## Future Enhancements

1. **Conversation Search**: Full-text search across all conversations
2. **Conversation Pinning**: Mark favorite conversations
3. **Conversation Export**: Export as JSON, PDF, Markdown
4. **Sharing**: Share conversations with team members
5. **Conversation Branching**: Create alternative conversation branches
6. **Auto-Summarization**: AI-generated conversation summaries
7. **Tags/Labels**: Organize conversations by topic
8. **Bulk Operations**: Archive/delete multiple conversations
9. **Conversation Analytics**: Stats on conversation patterns
10. **Context Window Optimization**: Smarter message selection for context

---

## Troubleshooting

### Conversation Not Loading
1. Check Firebase connectivity
2. Verify user has access to conversation
3. Check Redis availability (non-critical)
4. Clear browser cache and reload

### Messages Not Saving
1. Verify authentication token valid
2. Check Firestore write permissions
3. Check network connectivity
4. Review backend logs for errors

### Slow Conversation Load
1. Check Redis cache status
2. Monitor Firestore latency
3. Consider pagination for large conversations
4. Check message count (context size affects processing)

### Agent Losing Context
1. Verify conversation ID passed correctly
2. Check context formatting in backend
3. Review agent system context window size
4. Consider reducing max_messages parameter

---

## Testing Checklist

- [ ] Create new conversation - appears in sidebar
- [ ] Send message - creates conversation automatically
- [ ] Load existing conversation - all messages appear
- [ ] Context awareness - agent references earlier messages
- [ ] Archive conversation - moves to archived view
- [ ] Delete conversation - permanent removal
- [ ] Message timestamps - correct display
- [ ] Metadata tracking - agents_used, tasks_created logged
- [ ] Redis cache - conversation loads fast on reload
- [ ] Offline fallback - works without Redis
- [ ] Dark mode - readable in both themes
- [ ] Mobile view - sidebar toggles properly
- [ ] Long conversations - scrolling smooth, no lag
- [ ] Multiple users - conversations isolated per user
- [ ] Concurrent messages - no race conditions

---

## Files Modified

### Backend
- ✅ `app/models/conversation.py` - NEW
- ✅ `app/services/conversation_service.py` - NEW  
- ✅ `app/routes/agent.py` - UPDATED (added 5 new endpoints)
- ✅ `app/services/agent_service.py` - UPDATED (context parameter)

### Frontend
- ✅ `components/agent/ConversationList.tsx` - NEW
- ✅ `hooks/useConversations.ts` - NEW
- ✅ `pages/AgentPage.tsx` - REFACTORED (conversation support)

---

## Summary

The TaskTrail AI Agent now implements a robust conversation-by-conversation architecture with:

✅ **Persistent Storage**: All conversations saved in Firestore
✅ **Fast Retrieval**: Redis caching for 1-hour access patterns
✅ **Context Awareness**: Agent uses full conversation history
✅ **User-Friendly**: Sidebar for conversation management
✅ **Scalable**: Handles unlimited conversations per user
✅ **Reliable**: Graceful error handling and fallbacks
✅ **Testable**: Clear API contracts and data structures

This enables truly intelligent, context-aware conversations with the AI Agent while maintaining full audit trails of all interactions.
