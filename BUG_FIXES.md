# TaskTrail - Bug Fixes & Issues

## ✅ Fixed Issues

### 1. **Date Handling in Task Creation** 
**Status**: ✅ FIXED

**Problem**: Tasks were showing old dates (e.g., 07-10-2023) instead of the correct dates when created via AI agent.

**Solution**: 
- Added intelligent date parsing in `executor_agent.py` with function `_parse_relative_date()`
- Updated task tools to use flexible date parsing via `_parse_date_string()`
- Added better prompt instructions for the executor agent to provide dates in ISO format (YYYY-MM-DD)
- Handles natural language dates: "tomorrow", "next week", "next friday"

**Files Modified**:
- `backend/app/agents/executor_agent.py` - Enhanced with date parsing and better prompt
- `backend/app/agents/tools/task_tools.py` - Added date parsing utilities

### 2. **Calendar Task Display**
**Status**: ✅ FIXED

**Problem**: Calendar view wasn't displaying created tasks even though they were in the database.

**Solution**:
- Backend was returning ISO datetime strings but frontend expected JavaScript Date objects
- Added `parseTaskDates()` function in taskApi service
- All API responses now automatically convert string dates to Date objects
- Calendar component can now properly process task due dates

**Files Modified**:
- `frontend/src/services/taskApi.ts` - Added date parsing for all API responses

---

## ⚠️ Remaining Issues

### Firebase Composite Index Error

**Problem**: Backend logs show error when trying to list projects:
```
Error listing projects: 400 The query requires an index
```

**Root Cause**: Firestore needs a composite index for the projects query that filters on multiple fields: `isArchived`, `userId`, and `createdAt`

**Solution**: Create the composite index in Firebase Console

**Steps to Fix**:

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: `tasktrail-dev` (or your project name)
3. Navigate to **Firestore Database** → **Indexes**
4. Click on the link provided in the error message, OR
5. Manually create a composite index with:
   - **Collection**: `projects`
   - **Fields**:
     - `isArchived` (Ascending)
     - `userId` (Ascending)
     - `createdAt` (Descending)

Once created, the projects listing will work correctly and the agent will be able to access project information.

**Workaround** (Temporary): The agent can still create tasks without needing to list projects, but project organization features won't work until this is fixed.

---

## 🧪 Testing the Fixes

### Test Date Handling

1. Open the AI Agent chat
2. Try creating tasks with relative dates:
   - "Create a task to review code tomorrow"
   - "Create a task for next friday"
   - "Create a task in 3 days to test features"
3. Check that tasks appear with correct due dates

### Test Calendar Display

1. Go to Calendar view
2. Tasks should now appear on their respective due dates
3. Color coding by priority should display correctly
4. Clicking on tasks should show details

---

## 📝 Notes for Future Development

### Date Handling Best Practices
- Always use ISO format (YYYY-MM-DD) when sending dates to backend
- Frontend now automatically converts all dates from strings to Date objects
- Agent prompt includes today's date to help with relative date calculations

### API Response Handling
- All API responses that contain date fields are automatically parsed
- This prevents "Invalid Date" errors in the calendar and date displays
- Add similar parsing for any new date fields

### Firebase Configuration
- Keep composite indexes up to date when adding new query filters
- Firestore will provide helpful error messages with index creation links
- Some indexes are auto-generated, but complex multi-field queries need manual setup

---

## 🚀 Current Status

**Backend**: ✅ Running
- FastAPI server on `http://localhost:8000`
- Firebase authentication working
- AI agent system operational
- Date parsing improved

**Frontend**: ✅ Running
- Vite dev server on `http://localhost:5173`
- Date display fixed
- Calendar view ready

**Known Limitations**:
- Projects listing fails due to missing Firebase index (see above)
- Projects feature partially limited until index is created
- Task creation works fine even without project listing

---

## 🔧 Environment

- Python 3.x with FastAPI
- Node.js with React 19
- Firebase Firestore
- OpenAI API

**API Key Status**: ✅ OpenAI API key is configured in `.env`

---

**Last Updated**: January 26, 2026
