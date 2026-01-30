# Testing Guide

This guide covers the minimal, maintained test suite for TaskTrail.

---

## Prerequisites

### 1. Test user token (for auth tests)

Some tests require a **real Firebase ID token** from a signed-in user.

**Get a valid Firebase token:**
1. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
2. Sign in at http://localhost:5173
3. Open browser DevTools → Console and run:
   ```javascript
   localStorage.getItem('firebaseToken')
   ```
   If that returns `null`, try:
   ```javascript
   localStorage.getItem('authToken')
   ```
4. Add the token to [backend/.env](backend/.env):
   ```bash
   TEST_USER_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

---

## Run Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run targeted suites
```bash
# Admin auth tests
pytest tests/test_admin_auth.py -v

# Token tracking tests
pytest tests/test_token_tracking.py -v

# API endpoint tests
pytest tests/test_endpoints.py -v
```

### With coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

---

## Test Suites (Maintained)

### 1. Admin Auth Tests
- File: [tests/test_admin_auth.py](tests/test_admin_auth.py)
- Covers role validation, permission checks, and admin-only access.

### 2. Token Tracking Tests
- File: [tests/test_token_tracking.py](tests/test_token_tracking.py)
- Covers cost calculation, usage aggregation, and limits.

### 3. API Endpoint Tests
- File: [tests/test_endpoints.py](tests/test_endpoints.py)
- Covers authentication flow and core REST endpoints.

---

## Reset Database (Development Only)

To start with a clean slate:

```bash
cd backend
python reset_firebase.py
```

**Warning:** This deletes all development data.

---

## Troubleshooting

### "TEST_USER_TOKEN not set"
- Add your Firebase auth token to [backend/.env](backend/.env)
- Ensure [backend/.env](backend/.env) exists and is loaded

### "Connection refused"
- Ensure API is running: `docker compose up --build`

---

*Last Updated: January 30, 2026*
