# Testing Guide (Deprecated)

This guide moved to [docs/TESTING.md](docs/TESTING.md).

## Prerequisites

### 1. Set up test user token

For tests that require authentication, you need a **real Firebase ID token** from a signed-in user.

**How to get a valid Firebase token:**

1. **Start the frontend** (in a separate terminal):
   ```bash
   cd frontend
   npm run dev
   ```

2. **Sign in with a test user** at `http://localhost:5173`
   - Use an existing Firebase user account or create a new one
   - You should see the dashboard after successful login

3. **Get the Firebase ID token** from browser console:
   ```javascript
   // Open browser DevTools (F12) → Console tab and paste:
   localStorage.getItem('firebaseToken')
   // Or if that doesn't work, try:
   localStorage.getItem('authToken')
   // Or check what's available:
   console.log(localStorage)
   ```
   
   OR check Firebase auth directly:
   ```javascript
   // In browser console:
   import { getAuth } from 'firebase/auth';
   const auth = getAuth();
   auth.currentUser?.getIdToken().then(token => console.log(token));
   ```

4. **Add token to backend/.env**:
   ```bash
   # Copy the token from browser console and add to backend/.env
   TEST_USER_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

5. **Install test dependencies** (if not already done):
   ```bash
   pip install -r backend/requirements.txt
   ```

## Running Tests

### Run All Tests
```bash
cd tests
python run_tests.py
```

### Run Specific Test Suites
```bash
# Endpoint tests only
python run_tests.py endpoints

# Agent conversation tests only
python run_tests.py agent

# Memory tests only
python run_tests.py memory
```

### Run with Coverage
```bash
python run_tests.py --coverage
```

### Run with Verbose Output
```bash
python run_tests.py -v
```

## Test Suites

### 1. Endpoint Tests (`test_endpoints.py`)
Tests all REST API endpoints:
- ✅ Health checks
- ✅ Authentication
- ✅ Tasks CRUD
- ✅ Projects CRUD
- ✅ Memory/Analytics

### 2. Agent Conversation Tests (`test_agent_conversations.py`)
Tests the AI agent system with realistic scenarios:
- 💬 Normal conversations (greetings, help)
- ✅ Task creation (single, multiple, with details)
- 📁 Project with tasks creation
- 🔍 Query conversations ("what should I do today?")
- 🔄 Complex multi-turn workflows

### 3. Memory Tests (`test_memory.py`, `test_e2e_memory.py`)
Tests conversation memory and compaction:
- 💾 Message storage
- 🗜️ Memory compaction
- 🔍 Semantic search
- 📊 Analytics

## Reset Database Before Testing

To start with a clean slate:

```bash
cd backend
python reset_firebase.py
```

**⚠️ Warning:** This deletes ALL data! Only use in development.

## Example Test Output

```
🧪 Running AGENT tests
====================================================================

tests/test_agent_conversations.py::TestNormalConversations::test_greeting PASSED
🤖 Agent: Hello! I'm your TaskTrail AI assistant...

tests/test_agent_conversations.py::TestTaskCreationConversations::test_simple_task_creation PASSED
🤖 Agent: I've created the task "Review quarterly reports"...
✅ Task created: Review quarterly reports

====================================================================
✅ All tests passed!
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    cd tests
    python run_tests.py --coverage
```

## Troubleshooting

### "TEST_USER_TOKEN not set"
- Add your Firebase auth token to `.env` file
- Make sure `.env` is in the `backend/` directory

### "Connection refused" errors
- Make sure the backend server is running: `python run_dev.py`
- Or use TestClient which doesn't require a running server

### Agent tests timing out
- Increase timeout in pytest.ini
- Check your OpenAI API key is valid
- Verify internet connection

## Writing New Tests

### For Endpoints:
```python
def test_my_endpoint(self, auth_headers):
    response = client.get("/api/v1/my-endpoint", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### For Agent Conversations:
```python
def test_my_conversation(self, auth_headers):
    message_data = {
        "message": "Your test message",
        "conversation_id": None
    }
    response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    print(f"\n🤖 Agent: {data['message']}")
```

## Best Practices

1. **Use fixtures** for common setup (auth_headers, test data)
2. **Print agent responses** with `-s` flag to see conversation flow
3. **Clean up** test data after running (or use `reset_firebase.py`)
4. **Test edge cases** (invalid inputs, missing fields)
5. **Use descriptive test names** that explain what's being tested
