# Deployment & Setup Guide: Conversation-Enabled AI Agent

## Quick Start (5 minutes)

### Step 1: Backend Setup

```bash
cd backend

# Backend should already be running
# If not:
python run_dev.py
# ✓ FastAPI running on http://localhost:8000
# ✓ New endpoints active:
#   - POST /api/v1/agent/conversations
#   - GET /api/v1/agent/conversations
#   - POST /api/v1/agent/chat (updated)
#   - etc.
```

### Step 2: Frontend Setup

```bash
cd frontend

# Frontend should already be running
# If not:
npm run dev
# ✓ Vite running on http://localhost:5173
# ✓ New components loaded:
#   - ConversationList sidebar
#   - useConversations hook
#   - Enhanced AgentPage
```

### Step 3: Verify

1. Open http://localhost:5173 in browser
2. Navigate to **AI Agent** page (sidebar)
3. You should see:
   - ✅ Sidebar with "New Chat" button
   - ✅ Empty chat area with welcome message
   - ✅ Input field at bottom

4. Click **"New Chat"** → Type message → Send
5. You should see:
   - ✅ Conversation created in sidebar
   - ✅ Message sent and response received
   - ✅ Messages persisting in conversation

6. Switch conversations:
   - ✅ Create another conversation
   - ✅ Click first conversation in sidebar
   - ✅ Previous messages reappear

**If all ✅, deployment successful!**

---

## Detailed Deployment Steps

### Backend Deployment

#### Prerequisites
```bash
# Ensure these are installed
python --version          # 3.9+
pip list | grep fastapi   # Should show fastapi installed
pip list | grep google-cloud-firestore  # Should show firestore

# If missing, install:
pip install -r requirements.txt
```

#### Start Backend Server
```bash
cd backend

# Run development server
python run_dev.py

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
# INFO:     Route GET /api/v1/agent/conversations registered
# INFO:     Route POST /api/v1/agent/chat registered
# ... (all agent routes should show)
```

#### Verify Endpoints
```bash
# In another terminal, test endpoints:

# 1. Create conversation
curl -X POST http://localhost:8000/api/v1/agent/conversations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
# {"id": "uuid-xxx", "title": "New Conversation", "message_count": 0, ...}

# 2. List conversations
curl -X GET http://localhost:8000/api/v1/agent/conversations \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected response:
# [{"id": "uuid-xxx", "title": "...", "message_count": 0, ...}]
```

#### Database Setup

**Firestore:**
```firestore
# Ensure your Firestore database has this structure created:
# (auto-created by ConversationService on first write)

users/{uid}/conversations/{conversation_id}
├── id: string
├── title: string
├── messages: array
├── created_at: timestamp
├── updated_at: timestamp
├── archived: boolean
└── metadata: map
```

No manual setup needed - ConversationService creates on first use.

**Redis (Optional but Recommended):**
```bash
# If you have Redis running:
redis-cli ping
# Should respond: PONG

# ConversationService will auto-use it if available
# Otherwise gracefully falls back to Firestore only
```

### Frontend Deployment

#### Prerequisites
```bash
node --version           # 18+
npm --version           # 9+

# Verify new files exist:
ls frontend/src/components/agent/ConversationList.tsx
ls frontend/src/hooks/useConversations.ts
```

#### Start Frontend Server
```bash
cd frontend

# Install dependencies (if fresh)
npm install

# Run development server
npm run dev

# Expected output:
# VITE v5.x.x  ready in XXX ms
# ➜  Local:   http://localhost:5173/
# ➜  press h to show help
```

#### Verify Components
```javascript
// In browser console (F12 > Console):
// These should work without errors:

// 1. Check if ConversationList component loads
import { ConversationList } from './components/agent/ConversationList.tsx'
// No error = ✓

// 2. Check if useConversations hook loads
import { useConversations } from './hooks/useConversations'
// No error = ✓

// 3. Check network tab
// When loading /agent page, you should see API calls:
// GET /api/v1/agent/conversations (200)
```

### Integration Testing

#### Test Scenario 1: Create Conversation
```
1. Open http://localhost:5173
2. Navigate to "AI Agent"
3. Click "New Chat" button
4. Type: "Hello, how are you?"
5. Click Send

Expected:
- Conversation appears in sidebar with title
- Welcome message shows
- User message appears
- Assistant response appears
- No console errors
```

#### Test Scenario 2: Persistence
```
1. Continue from above
2. Refresh page (F5)
3. Agent page loads

Expected:
- Previous conversation still in sidebar
- Messages still visible
- Click different conversation
- Previous messages appear
```

#### Test Scenario 3: Context Awareness
```
1. Create new conversation
2. Type: "I want to build a website"
3. Send and wait for response
4. Type: "Break that down into steps"
5. Send

Expected:
- Agent remembers "website" from first message
- Provides breakdown relevant to website project
- No ambiguity about what to break down
```

#### Test Scenario 4: Archive/Delete
```
1. In sidebar, hover over conversation
2. Click archive icon
3. Toggle "Show Archived"

Expected:
- Conversation disappears from active
- Reappears in archived view
- Click delete to permanently remove
```

---

## Troubleshooting

### Backend Issues

#### Issue: "ModuleNotFoundError: No module named 'app.models.conversation'"

**Solution:**
```bash
# Ensure file exists:
ls -la backend/app/models/conversation.py

# If missing, file was not created. Re-create:
# See "Files Created" section in implementation guide

# Clear Python cache:
find . -type d -name __pycache__ -exec rm -r {} +
python run_dev.py
```

#### Issue: "Cannot import ConversationService"

**Solution:**
```bash
# Ensure conversation_service.py exists:
ls -la backend/app/services/conversation_service.py

# Verify agent.py imports correctly:
grep "from app.services.conversation_service" backend/app/routes/agent.py

# Should show:
# from app.services.conversation_service import ConversationService
```

#### Issue: Firestore "Permission denied" error

**Solution:**
```
1. Ensure serviceAccountKey.json in backend/
2. Verify Firebase credentials valid (not expired)
3. Check Firestore rules allow write to users/{uid}/conversations
4. Rule should be:
   match /users/{uid}/conversations/{document=**} {
     allow read, write: if request.auth.uid == uid;
   }
```

#### Issue: Redis connection refused

**Solution:**
```
# Redis is optional. If not available:
# ConversationService will still work with just Firestore
# You'll see warning in logs:
# "WARNING: Redis not available: connection refused"
# This is OK - caching just won't be used

# To enable Redis:
# 1. Start Redis: redis-server
# 2. Verify: redis-cli ping → PONG
# 3. Restart backend: python run_dev.py
```

### Frontend Issues

#### Issue: "Module not found: ConversationList"

**Solution:**
```bash
# Verify file exists:
ls -la frontend/src/components/agent/ConversationList.tsx

# If missing, re-create from implementation guide

# Clear frontend cache:
rm -rf frontend/.cache frontend/node_modules/.vite
npm run dev
```

#### Issue: "useConversations is not a function"

**Solution:**
```bash
# Verify hook file exists:
ls -la frontend/src/hooks/useConversations.ts

# Verify import path in AgentPage.tsx:
grep "useConversations" frontend/src/pages/AgentPage.tsx

# Should show:
# import { useConversations } from '../hooks/useConversations';

# Check for syntax errors:
npm run lint
```

#### Issue: Conversations not loading in sidebar

**Solution:**
```javascript
// Check browser console for errors (F12 > Console)
// Should show API calls like:
// GET /api/v1/agent/conversations 200 OK

// If getting 404:
// - Verify backend routes are loaded
// - Restart backend: python run_dev.py

// If getting 401:
// - User not authenticated
// - Log in first
// - Check auth token in Network tab

// If empty list:
// - No conversations yet (normal for new user)
// - Click "New Chat" to create first one
```

#### Issue: Messages showing but not persisting after refresh

**Solution:**
```javascript
// Check Firestore:
// Firebase Console > Firestore > users > {your-uid} > conversations
// Should see conversation document with messages array

// If not there:
// - Check backend logs for errors
// - Verify Firestore write succeeded (should see 200 response)
// - Check authentication is valid

// Verify API response includes conversation_id:
// Network tab > Find POST /api/v1/agent/chat
// Response should have: "conversation_id": "uuid-xxx"
```

### API Issues

#### Issue: POST /api/v1/agent/chat returns 500 error

**Solution:**
```bash
# Check backend logs for error message
# Should show something like:
# ERROR: Agent chat error: ...

# Common causes:
# 1. conversation_service.py has syntax error
#    → Run: python -m py_compile backend/app/services/conversation_service.py

# 2. ConversationService import missing
#    → Check agent.py has: from app.services.conversation_service import ConversationService

# 3. Firestore permissions
#    → Verify user can write to conversations
#    → Check rules in Firebase Console

# 4. Agent service error
#    → Verify agent system still working
#    → Test with simple message
```

#### Issue: GET /api/v1/agent/conversations returns 404

**Solution:**
```bash
# Endpoint name changed or not loaded

# Verify route is registered:
# Start backend and look for:
# "Route GET /api/v1/agent/conversations registered"

# Check routes/agent.py has:
grep "@router.get(\"/conversations\")" backend/app/routes/agent.py

# If not there, endpoint definition missing - re-create from guide
```

---

## Configuration

### Customize Conversation Behavior

#### Max Messages for Context
```python
# File: backend/app/routes/agent.py
# Find: conversation_service.get_conversation_context(...)
# Change max_messages parameter:

# Default: 20
context = conversation_service.get_conversation_context(conversation_id, max_messages=20)

# For longer context (slower):
context = conversation_service.get_conversation_context(conversation_id, max_messages=50)

# For shorter context (faster):
context = conversation_service.get_conversation_context(conversation_id, max_messages=10)
```

#### Redis Cache TTL
```python
# File: backend/app/services/conversation_service.py
# Find: self.redis_client.setex(...)
# Change TTL (in seconds):

# Default: 3600 (1 hour)
self.redis_client.setex(key, 3600, value)

# Longer cache (4 hours):
self.redis_client.setex(key, 14400, value)

# Shorter cache (15 minutes):
self.redis_client.setex(key, 900, value)
```

#### Sidebar Conversation Limit
```typescript
// File: frontend/src/components/agent/ConversationList.tsx
// Find: fetchConversations() function
// Change limit parameter:

// Default: 50 conversations shown
const response = await api.get(`/api/v1/agent/conversations?archived=${showArchived}`);

// Show more:
const response = await api.get(`/api/v1/agent/conversations?limit=100&archived=${showArchived}`);

// Show fewer:
const response = await api.get(`/api/v1/agent/conversations?limit=20&archived=${showArchived}`);
```

---

## Performance Optimization

### For Large Conversation Counts
```python
# Firestore Indexes (auto-created, no action needed):
# - conversations ordered by updated_at DESC
# - conversations filtered by archived

# Add pagination:
# GET /api/v1/agent/conversations?limit=20&page=2
# (Future enhancement)
```

### For Long Conversations
```python
# Reduce context window:
# agents see fewer messages = faster processing
# change max_messages from 20 to 10

# Or use smarter selection:
# Only include user messages, skip some assistant responses
# (Future enhancement)
```

### For Many Users
```
Firestore auto-scales
Redis capacity depends on your instance

Monitor:
- Firestore: Check quota in Firebase Console
- Redis: Use redis-cli INFO to check memory usage
```

---

## Monitoring

### Firestore Usage
```
Firebase Console:
1. Go to Firestore > Data tab
2. Navigate to users > {uid} > conversations
3. Check number of documents
4. Monitor read/write operations in Firestore > Usage

Expected:
- ~1 KB per conversation (increases with messages)
- 1 read per conversation load
- 1 write per message sent
```

### Redis Usage
```bash
# Check cache hit rate
redis-cli INFO stats | grep hits
redis-cli INFO stats | grep misses

# Check memory usage
redis-cli INFO memory | grep used_memory_human

# Monitor in real-time
redis-cli MONITOR
# (Ctrl+C to stop)
```

### Backend Logs
```bash
# Tail logs while running
tail -f logs/backend.log

# Or watch FastAPI output
# Should see patterns like:
# "INFO: Created conversation xxx"
# "INFO: Added user message to conversation xxx"
# "DEBUG: Retrieved conversation xxx from Redis"
```

---

## Rollback (If Needed)

If you need to revert to the single-conversation agent:

```bash
# Backend
cd backend
git checkout app/routes/agent.py
git checkout app/services/agent_service.py
rm app/models/conversation.py
rm app/services/conversation_service.py
python run_dev.py

# Frontend
cd frontend
git checkout src/pages/AgentPage.tsx
rm src/components/agent/ConversationList.tsx
rm src/hooks/useConversations.ts
npm run dev
```

---

## Production Deployment

### Before Going Live

#### Checklist
- [ ] All API endpoints tested
- [ ] Firestore security rules configured
- [ ] Redis cluster set up (if using)
- [ ] Firebase quotas reviewed
- [ ] Error handling verified
- [ ] Load testing completed
- [ ] Monitoring dashboards created
- [ ] Backup strategy in place
- [ ] Documentation reviewed by team
- [ ] User training completed

#### Firestore Rules
```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{uid}/conversations/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
  }
}
```

#### Environment Variables
```bash
# backend/.env
FIREBASE_PROJECT_ID=your-project
FIRESTORE_DATABASE=default
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_DB=1

# frontend/.env
VITE_API_URL=https://api.example.com
VITE_FIREBASE_PROJECT=your-project
```

#### Deployment Script
```bash
#!/bin/bash
# deploy.sh

# Backend
cd backend
git pull origin main
python -m pip install --upgrade -r requirements.txt
python run_dev.py &

# Frontend
cd ../frontend
git pull origin main
npm install
npm run build
# Deploy dist/ folder to hosting

echo "Deployment complete"
```

---

## Support Resources

### Documentation Files
- `AI_AGENT_CONVERSATION_ARCHITECTURE.md` - Technical deep dive
- `AI_AGENT_CONVERSATIONS_QUICK_START.md` - User & developer guide
- `AI_AGENT_TEST_PLAN.md` - Comprehensive testing guide
- `AI_AGENT_IMPLEMENTATION_COMPLETE.md` - Overview and summary

### Getting Help
1. Check Firestore Console for conversation data
2. Review backend logs for errors
3. Check browser console (F12) for frontend errors
4. Review network tab to see API responses
5. Test manually with cURL

### Common Tasks

**Reset all conversations (development):**
```bash
# Firestore: Select all conversations, delete in batches
# Redis: redis-cli FLUSHDB 1
```

**Test with production data:**
```bash
# Export conversations:
firebase firestore:export --project=your-project --export-path=/path

# Import later:
firebase firestore:restore --project=your-project --backup-path=/path
```

---

## Next Steps

1. ✅ **Deployed** the conversation system
2. ✅ **Tested** all features work correctly
3. 📊 **Monitor** Firestore and Redis usage
4. 📈 **Gather** user feedback
5. 🚀 **Optimize** based on usage patterns
6. 🔄 **Iterate** on future enhancements

---

**Deployment Complete!** 🎉

Your AI Agent now has full conversation support with persistent storage and context awareness. Users can maintain multiple conversations and pick up right where they left off!
