# TaskTrail - Complete Setup & Testing Guide

**Status:** ✅ READY FOR COMPREHENSIVE TESTING

**Last Updated:** January 29, 2026

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis running locally (for vector memory)
- Firebase credentials (serviceAccountKey.json)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure Firebase
# Make sure serviceAccountKey.json is in backend/ directory

# Start backend server
python run_dev.py
# Server runs on http://localhost:8000
```

**Verify Backend:**
```bash
curl http://localhost:8000/docs
# Should see Swagger/OpenAPI documentation
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Open http://localhost:5173 in browser
```

**Verify Frontend:**
- Should see login page
- Can navigate without errors

---

## 🧪 Testing Workflow

### Phase 1: Authentication Testing

**Steps:**
1. Open http://localhost:5173
2. Register new account or login
3. Should redirect to Dashboard

**Expected Results:**
- ✅ Login form displays correctly
- ✅ Registration creates new user
- ✅ JWT token stored in localStorage
- ✅ Protected routes redirect to login if not authenticated

---

### Phase 2: Memory Features Testing

#### Test 2.1: Memory Stats Widget
**Test Location:** Dashboard page

**Steps:**
1. Navigate to Dashboard (should be default page)
2. Look for Memory Stats Widget in top-right section
3. Observe stats displayed:
   - Total messages
   - Messages this week
   - Vector memory status
   - Compaction recommendation

**Verification:**
```bash
# Check backend memory stats endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/memory/stats
```

**Expected Response:**
```json
{
  "total_messages": 42,
  "messages_this_week": 12,
  "compact_history": [],
  "vector_memory_status": "healthy",
  "last_compaction": "2026-01-29T10:30:00",
  "next_compaction": "2026-01-30T03:00:00"
}
```

**Test Outcomes:**
- [ ] Widget loads without errors
- [ ] Stats display correctly
- [ ] Auto-refresh works (60 second interval)
- [ ] Dark mode styling correct

---

#### Test 2.2: Export Functionality
**Test Location:** Dashboard page

**Steps:**
1. Click "Export Data" button (next to Memory Stats Widget)
2. Select export format:
   - JSON (default)
   - CSV
   - Markdown
3. Click "Export" button
4. Verify file downloads

**Test JSON Export:**
- Download file named `conversations_YYYYMMDD.json`
- Open file and verify JSON structure:
  ```json
  {
    "exported_at": "2026-01-29T...",
    "format_version": "1.0",
    "total_messages": 42,
    "conversations": [...]
  }
  ```

**Test CSV Export:**
- Download file named `conversations_YYYYMMDD.csv`
- Open in spreadsheet application
- Verify columns: date, agent_type, message, project_id, task_id

**Test Markdown Export:**
- Download file named `conversations_YYYYMMDD.md`
- Open in text editor
- Verify markdown formatting with headers and sections

**Test Outcomes:**
- [ ] All three formats download successfully
- [ ] File content is valid for each format
- [ ] Proper file naming with dates
- [ ] No errors in browser console

---

#### Test 2.3: Memory Timeline
**Test Location:** Backend endpoint test

**Steps:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Run:
```javascript
const response = await fetch('/api/v1/memory/timeline');
const data = await response.json();
console.log(data);
```

**Expected Response:**
```json
{
  "timeline": [
    { "date": "2026-01-29", "count": 8 },
    { "date": "2026-01-28", "count": 12 },
    ...
  ]
}
```

**Test Outcomes:**
- [ ] Timeline data returns successfully
- [ ] Dates are properly formatted
- [ ] Message counts are positive integers

---

### Phase 3: Projects Management Testing

#### Test 3.1: View Projects
**Test Location:** Projects page

**Steps:**
1. Click "Projects" in sidebar navigation
2. Should see grid of existing projects (if any)
3. Observe layout:
   - Desktop: 3 columns
   - Tablet: 2 columns
   - Mobile: 1 column

**Test Outcomes:**
- [ ] Projects page loads without errors
- [ ] Responsive grid layout works
- [ ] Color coding displays correctly
- [ ] Message counts show per project

---

#### Test 3.2: Create New Project
**Test Location:** Projects page

**Steps:**
1. Go to Projects page
2. Fill in "New Project" form:
   - Enter project name (e.g., "Website Redesign")
   - Select color (click color buttons)
   - Click "Create Project" button
3. New project should appear in grid

**Verify Backend:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/projects
```

**Test Outcomes:**
- [ ] Form submission works
- [ ] Project appears in list immediately
- [ ] Color selection saves correctly
- [ ] Backend creates project in database

---

#### Test 3.3: Export Project Conversations
**Test Location:** Projects page

**Steps:**
1. Click "Export" button on any project card
2. Select export format
3. Click "Export" button in dialog
4. File should download

**Expected Filename:** `project_conversations_YYYYMMDD.json|csv|md`

**Verify Content:**
- Should only contain messages from that project
- Should include project metadata
- Should be properly formatted

**Test Outcomes:**
- [ ] Export dialog appears correctly
- [ ] File downloads with correct name
- [ ] Content is scoped to project
- [ ] Format matches selection

---

#### Test 3.4: View Project Tasks
**Test Location:** Projects page

**Steps:**
1. Click "View Tasks" button on any project card
2. Should navigate to Tasks page filtered by project (if implemented)
3. Should show only tasks for that project

**Test Outcomes:**
- [ ] Navigation works
- [ ] Tasks filter by project (if implemented)
- [ ] Proper route handling

---

#### Test 3.5: Delete Project
**Test Location:** Projects page

**Steps:**
1. Click delete button (trash icon) on any project card
2. Confirmation dialog should appear
3. Confirm deletion
4. Project should disappear from list

**Verify Backend:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -X DELETE http://localhost:8000/api/v1/projects/{project_id}
```

**Test Outcomes:**
- [ ] Delete confirmation dialog appears
- [ ] Project removes from UI
- [ ] Backend deletes project
- [ ] Associated tasks handled (cascaded or orphaned)

---

### Phase 4: Task Management Testing

#### Test 4.1: Create Task
**Test Location:** Tasks page

**Steps:**
1. Go to Tasks page
2. Click "Add Task" button
3. Fill in task details:
   - Title
   - Description (optional)
   - Due date
   - Project (if available)
   - Priority
4. Click "Create" button

**Expected Results:**
- Task appears in list
- Shows correct status (e.g., "To Do")
- Color-coded by priority

**Test Outcomes:**
- [ ] Form validation works
- [ ] Task creation succeeds
- [ ] Task displays in list
- [ ] Project association works (if available)

---

#### Test 4.2: Update Task
**Test Location:** Tasks page

**Steps:**
1. Click on any task to open details
2. Edit fields:
   - Status (drag or select)
   - Title/Description
   - Due date
   - Priority
3. Changes should auto-save

**Test Outcomes:**
- [ ] Task details load
- [ ] Edits update correctly
- [ ] Status changes reflect in list
- [ ] Changes persist on page reload

---

#### Test 4.3: Task Status Workflow
**Test Location:** Kanban page or Tasks page

**Steps:**
1. Navigate to Kanban page
2. Drag task between columns:
   - To Do → In Progress
   - In Progress → Done
3. Task should update in backend
4. Status should reflect in Dashboard stats

**Test Outcomes:**
- [ ] Drag-and-drop works
- [ ] Status updates persist
- [ ] Dashboard stats update
- [ ] Completion rate changes

---

### Phase 5: Dashboard Integration Testing

#### Test 5.1: Dashboard Stats
**Test Location:** Dashboard page

**Steps:**
1. Go to Dashboard
2. Check hero card stats:
   - Total tasks count
   - In progress count
   - To do count
   - Completion percentage
3. Modify some tasks (create, delete, change status)
4. Stats should update (or refresh page)

**Test Outcomes:**
- [ ] Stats display correctly
- [ ] Counts are accurate
- [ ] Percentage calculation correct
- [ ] Color coding matches task status

---

#### Test 5.2: Quick Actions
**Test Location:** Dashboard page

**Steps:**
1. Review "Quick Actions" grid
2. Click each action button:
   - "View Tasks" → Tasks page
   - "Calendar View" → Calendar page
   - "Create Project" → Opens project creation
   - "Browse Agents" → Agents page
3. Should navigate to correct page or open dialog

**Test Outcomes:**
- [ ] All buttons navigate correctly
- [ ] Icons display properly
- [ ] Hover effects work
- [ ] Mobile layout is usable

---

#### Test 5.3: Recent Activity
**Test Location:** Dashboard page

**Steps:**
1. Review "Recent Activity" section
2. Should show latest 5 tasks
3. Each task shows:
   - Status indicator (color dot)
   - Task title
   - Task status
   - Due date (if set)

**Test Outcomes:**
- [ ] Activity list loads
- [ ] Shows correct tasks
- [ ] Status colors correct
- [ ] Due dates formatted properly

---

### Phase 6: Navigation & UI Testing

#### Test 6.1: Sidebar Navigation
**Test Location:** All pages

**Steps:**
1. Click each sidebar item:
   - Dashboard
   - Today
   - Tasks
   - Projects (new)
   - Kanban
   - Calendar
2. Each should navigate to correct page

**Test Outcomes:**
- [ ] All nav items work
- [ ] Active state highlights correctly
- [ ] Projects item appears in navigation
- [ ] Folder icon displays

---

#### Test 6.2: Dark Mode
**Test Location:** All pages

**Steps:**
1. Click theme toggle (moon/sun icon)
2. Page should switch to dark mode
3. Check all new components:
   - Memory Stats Widget
   - Export Dialog
   - Projects page
4. Colors should be readable
5. Gradients should look good

**Test Outcomes:**
- [ ] Dark mode toggle works
- [ ] All components switch themes
- [ ] Colors remain readable
- [ ] No styling issues

---

#### Test 6.3: Responsive Design
**Test Location:** All pages

**Steps:**
1. Open DevTools (F12)
2. Test at different breakpoints:
   - Mobile: 375px width
   - Tablet: 768px width
   - Desktop: 1024px+ width
3. Check each page:
   - Dashboard
   - Projects
   - Tasks
   - Kanban

**Test Outcomes:**
- [ ] Layout adapts to screen size
- [ ] Text readable on mobile
- [ ] Touch targets adequate size
- [ ] No horizontal scroll

---

### Phase 7: Backend Memory System Testing

#### Test 7.1: Memory Storage
**Test Location:** Backend

**Steps:**
1. Ensure conversations are happening (create tasks, messages)
2. Run backend test:
```bash
cd backend
python -m pytest tests/test_memory.py -v
```

**Expected Results:**
- All memory tests pass
- Conversations stored correctly
- Filtering works

**Test Outcomes:**
- [ ] All tests pass
- [ ] No memory leaks
- [ ] Data persists

---

#### Test 7.2: Memory Compaction
**Test Location:** Backend

**Steps:**
1. Check scheduled compaction jobs:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/memory/health
```

2. Run compaction manually (if endpoint available):
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/memory/compact
```

**Expected Results:**
- Compaction removes old conversations
- Memory stats update
- No data loss

**Test Outcomes:**
- [ ] Compaction scheduled correctly
- [ ] Manual compaction works
- [ ] Memory stats reflect compaction

---

#### Test 7.3: Vector Memory
**Test Location:** Backend

**Steps:**
1. Create several conversations
2. Test vector search:
```bash
curl -G -H "Authorization: Bearer YOUR_TOKEN" \
  -d "query=task%20management" \
  http://localhost:8000/api/v1/memory/search
```

**Expected Results:**
- Search returns relevant conversations
- Embeddings work correctly
- Filtering by project/task works

**Test Outcomes:**
- [ ] Vector search functional
- [ ] Embeddings generate correctly
- [ ] Filters work on vector results

---

## 📊 Test Results Tracking

### Create a test log file:

```markdown
# Testing Results Log

## Date: [Test Date]
## Tester: [Your Name]

### Phase 1: Authentication
- [ ] Login works
- [ ] Register works
- [ ] Protected routes work

### Phase 2: Memory Features
- [ ] Memory Stats Widget loads
- [ ] Export JSON works
- [ ] Export CSV works
- [ ] Export Markdown works
- [ ] Timeline endpoint returns data

### Phase 3: Projects
- [ ] Projects page loads
- [ ] Create project works
- [ ] Delete project works
- [ ] Export project works
- [ ] View tasks works

### Phase 4: Tasks
- [ ] Create task works
- [ ] Update task works
- [ ] Delete task works
- [ ] Change status works

### Phase 5: Dashboard
- [ ] Stats display correctly
- [ ] Quick actions work
- [ ] Recent activity shows
- [ ] Memory widget auto-refreshes

### Phase 6: UI/Navigation
- [ ] Sidebar navigation works
- [ ] Dark mode works
- [ ] Responsive layout works
- [ ] All icons display

### Phase 7: Backend
- [ ] Memory tests pass
- [ ] Compaction works
- [ ] Vector search works

## Issues Found:
[List any issues discovered]

## Notes:
[Additional observations]
```

---

## 🐛 Troubleshooting

### Issue: Memory Widget Not Loading
**Solution:**
1. Check backend is running: `curl http://localhost:8000/api/v1/memory/stats`
2. Check browser console for errors
3. Verify authentication token is valid
4. Check CORS settings in backend

### Issue: Projects Not Displaying
**Solution:**
1. Verify backend projects endpoint: `curl http://localhost:8000/api/v1/projects`
2. Check if backend created projects schema
3. Verify authentication in API calls

### Issue: Export Downloads Empty/Invalid Files
**Solution:**
1. Check backend export endpoints
2. Verify conversation data exists
3. Check response headers (Content-Type, Content-Disposition)
4. Inspect network response in DevTools

### Issue: Dark Mode Not Switching
**Solution:**
1. Check ThemeContext provider in App.tsx
2. Verify localStorage persistence
3. Check Tailwind dark mode configuration
4. Clear browser cache and reload

### Issue: Tasks Not Updating
**Solution:**
1. Check backend tasks endpoints
2. Verify task_id in request
3. Check authentication token
4. Verify database connection

---

## 🚀 Performance Testing

### Frontend Performance
```javascript
// In browser console:
performance.mark('start');
// [perform action]
performance.mark('end');
performance.measure('action', 'start', 'end');
console.log(performance.getEntriesByName('action')[0].duration, 'ms');
```

**Target Metrics:**
- Page load: < 2 seconds
- Route navigation: < 500ms
- API calls: < 1 second
- Memory stats refresh: < 2 seconds

### Backend Performance
```bash
# Monitor backend memory
while true; do
  curl -s http://localhost:8000/api/v1/memory/stats | jq .
  sleep 5
done
```

---

## ✅ Sign-Off Checklist

- [ ] All phases tested
- [ ] No critical bugs found
- [ ] Performance acceptable
- [ ] Dark mode works
- [ ] Responsive design verified
- [ ] All new features working
- [ ] Backend stable
- [ ] Frontend responsive
- [ ] Export functionality tested
- [ ] Projects management tested

---

## 📝 Next Steps After Testing

1. **Fix any identified bugs**
2. **Optimize performance** if needed
3. **Add additional features**:
   - Memory timeline chart
   - Agent statistics dashboard
   - Project analytics
4. **Deploy to production**
5. **Monitor performance** in production

---

