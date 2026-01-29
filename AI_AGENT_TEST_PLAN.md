# AI Agent Comprehensive Testing Guide

## Overview
The TaskTrail AI Agent is powered by a sophisticated **LangGraph multi-agent system** with 5 specialized agents:
- **Supervisor**: Routes requests to appropriate agents
- **Planner**: Breaks down complex projects into subtasks
- **Executor**: Creates, updates, and deletes tasks
- **Query**: Searches and filters tasks with natural language
- **Conversation**: General help and Q&A

---

## Test Categories

### 1. BASIC CONVERSATION TESTS
Test fundamental conversation abilities and error handling.

#### 1.1 Simple Greetings
- **Input**: "Hi there"
- **Expected**: Friendly greeting acknowledging it's the TaskTrail assistant
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Hello, how are you?"
- **Expected**: Friendly response about being ready to help
- **Test Result**: ✓ PASS / ✗ FAIL

#### 1.2 Basic Questions
- **Input**: "What can you do?"
- **Expected**: List of capabilities (task creation, queries, updates, etc.)
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Help me get started"
- **Expected**: Explanation of how to use the agent
- **Test Result**: ✓ PASS / ✗ FAIL

#### 1.3 Attitude/Rudeness Handling
- **Input**: "You're useless"
- **Expected**: Professional, helpful response that doesn't take offense
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "I don't need your help"
- **Expected**: Respectful response, offers help when needed
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 2. TASK CREATION TESTS
Test the Executor agent's ability to create tasks from natural language.

#### 2.1 Simple Task Creation
- **Input**: "Create a task to buy groceries"
- **Expected**: Confirmation of task creation, possibly showing created task details
- **Test Result**: ✓ PASS / ✗ FAIL
- **Verification**: Check Tasks page to confirm task appears

- **Input**: "Add a new task: Call mom tomorrow"
- **Expected**: Task created with due date of tomorrow
- **Test Result**: ✓ PASS / ✗ FAIL

#### 2.2 Task Creation with Properties
- **Input**: "Create a high priority task to finish the report by Friday"
- **Expected**: Task created with:
  - Title: "finish the report" or similar
  - Priority: high
  - Due date: Friday (calculated date)
- **Test Result**: ✓ PASS / ✗ FAIL
- **Verification**: Check task details in Tasks page

- **Input**: "Add a task: Code review for John, due tomorrow, medium priority"
- **Expected**: All properties set correctly
- **Test Result**: ✓ PASS / ✗ FAIL

#### 2.3 Task Creation with Dates
- **Input**: "Create a task for next Monday"
- **Expected**: Due date automatically set to next Monday
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Task: Meeting prep, due in 3 days"
- **Expected**: Due date set to 3 days from today
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Create a task due December 25th"
- **Expected**: Handles specific calendar dates
- **Test Result**: ✓ PASS / ✗ FAIL

#### 2.4 Batch Task Creation
- **Input**: "Create 3 tasks: email client, review budget, prepare slides"
- **Expected**: All three tasks created separately
- **Test Result**: ✓ PASS / ✗ FAIL
- **Verification**: Should see 3 new tasks in the system

---

### 3. TASK QUERY TESTS
Test the Query agent's ability to search and filter tasks naturally.

#### 3.1 Simple Queries
- **Input**: "Show me my tasks"
- **Expected**: List of all current tasks
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "What are my tasks for today?"
- **Expected**: Only today's tasks listed
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Show overdue tasks"
- **Expected**: Only overdue tasks displayed
- **Test Result**: ✓ PASS / ✗ FAIL

#### 3.2 Advanced Filtering
- **Input**: "Show me high priority tasks"
- **Expected**: Only high-priority tasks shown
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "List tasks due this week"
- **Expected**: Tasks with due dates within the next 7 days
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "What tasks are assigned to my project?"
- **Expected**: Tasks filtered by project (if user has projects)
- **Test Result**: ✓ PASS / ✗ FAIL

#### 3.3 Natural Language Queries
- **Input**: "I need to see incomplete tasks"
- **Expected**: Tasks with status not "done"/"completed"
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Which tasks have I completed?"
- **Expected**: Only completed/done tasks
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "What's urgent?"
- **Expected**: High priority and/or overdue tasks
- **Test Result**: ✓ PASS / ✗ FAIL

#### 3.4 Count/Summary Queries
- **Input**: "How many tasks do I have?"
- **Expected**: Total count of tasks
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "How many are overdue?"
- **Expected**: Count of overdue tasks
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "What's my task completion rate?"
- **Expected**: Percentage of completed tasks
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 4. TASK UPDATE TESTS
Test the Executor agent's ability to modify existing tasks.

#### 4.1 Status Updates
- **Input**: "Mark 'Buy groceries' as complete"
- **Expected**: Task status changed to done/completed
- **Test Result**: ✓ PASS / ✗ FAIL
- **Verification**: Task should disappear from Today view or show as done

- **Input**: "I finished the report task"
- **Expected**: Correct task marked as done
- **Test Result**: ✓ PASS / ✗ FAIL

#### 4.2 Priority Updates
- **Input**: "Change 'Meeting prep' priority to high"
- **Expected**: Task priority updated to high
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Make 'Email client' low priority"
- **Expected**: Priority set to low
- **Test Result**: ✓ PASS / ✗ FAIL

#### 4.3 Due Date Updates
- **Input**: "Move 'Review budget' due date to next week"
- **Expected**: Task due date updated to next week
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "When is 'Code review' due? Change it to tomorrow"
- **Expected**: Shows current due date, then updates to tomorrow
- **Test Result**: ✓ PASS / ✗ FAIL

#### 4.4 Description Updates
- **Input**: "Update 'Meeting prep' with description: prepare agenda and slides"
- **Expected**: Task description updated with details
- **Test Result**: ✓ PASS / ✗ FAIL

#### 4.5 Task Deletion
- **Input**: "Delete 'Buy groceries'"
- **Expected**: Task removed from system
- **Test Result**: ✓ PASS / ✗ FAIL
- **Verification**: Task should not appear in task list

- **Input**: "Remove the 'Email client' task"
- **Expected**: Confirmed deletion
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 5. TASK BREAKDOWN / PLANNING TESTS
Test the Planner agent's ability to decompose complex tasks.

#### 5.1 Simple Breakdowns
- **Input**: "Break down 'Buy groceries' into steps"
- **Expected**: Subtasks like: make list, go to store, check out, etc.
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "How can I split the 'Report' task?"
- **Expected**: Suggested decomposition with concrete steps
- **Test Result**: ✓ PASS / ✗ FAIL

#### 5.2 Complex Project Planning
- **Input**: "Break down 'Launch product' into manageable tasks"
- **Expected**: Multiple steps covering planning, dev, testing, marketing, launch
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "How should I organize 'Website redesign'?"
- **Expected**: Logical breakdown: design, development, testing, deployment
- **Test Result**: ✓ PASS / ✗ FAIL

#### 5.3 Create and Execute Breakdown
- **Input**: "Break down 'Prepare presentation' and create tasks for each step"
- **Expected**: Creates multiple tasks from suggested breakdown
- **Test Result**: ✓ PASS / ✗ FAIL
- **Verification**: New tasks should appear in task list

---

### 6. SMART SUGGESTIONS TESTS
Test the Conversation agent's ability to provide AI-powered recommendations.

#### 6.1 Productivity Advice
- **Input**: "What should I focus on today?"
- **Expected**: Prioritized recommendations based on current tasks
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "How should I organize my work?"
- **Expected**: General productivity advice
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Give me productivity tips"
- **Expected**: Actionable advice for task management
- **Test Result**: ✓ PASS / ✗ FAIL

#### 6.2 Context-Aware Suggestions
- **Input**: "I'm overwhelmed with tasks, what should I do?"
- **Expected**: Suggests prioritization, breakdowns, or delegation strategies
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "How can I better manage my workload?"
- **Expected**: Personalized recommendations
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 7. EDGE CASES & ROBUSTNESS TESTS

#### 7.1 Ambiguous Input
- **Input**: "Task"
- **Expected**: Asks for clarification about what to do
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "It"
- **Expected**: Asks for clarification
- **Test Result**: ✓ PASS / ✗ FAIL

#### 7.2 Partial/Incomplete Requests
- **Input**: "Create a task"
- **Expected**: Asks what task should be created
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Change to high priority"
- **Expected**: Asks which task to update
- **Test Result**: ✓ PASS / ✗ FAIL

#### 7.3 Invalid/Impossible Requests
- **Input**: "Delete task with ID 999999"
- **Expected**: Gracefully handles non-existent task
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Set due date to 'banana'"
- **Expected**: Politely indicates invalid date format
- **Test Result**: ✓ PASS / ✗ FAIL

#### 7.4 Multi-turn Conversations
- **Input**: "Show me my high priority tasks"
- **Expected**: List shown

- **Input**: "Make the first one due tomorrow"
- **Expected**: Correctly understands reference to previous task
- **Test Result**: ✓ PASS / ✗ FAIL

#### 7.5 Long Messages
- **Input**: "Create several tasks for next week: Monday - call John to discuss project timeline, Tuesday - prepare budget spreadsheet for review, Wednesday - team meeting at 2pm, Thursday - finish documentation, Friday - client presentation"
- **Expected**: All tasks created with correct dates
- **Test Result**: ✓ PASS / ✗ FAIL

#### 7.6 Special Characters & Formatting
- **Input**: "Create task: 'Finish @project #urgent'"
- **Expected**: Handles special characters and hashtags properly
- **Test Result**: ✓ PASS / ✗ FAIL

- **Input**: "Task with emoji: 🎯 Complete the goal"
- **Expected**: Properly handles emoji in task title
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 8. CONVERSATION MEMORY & CONTEXT TESTS

#### 8.1 Context Persistence
- **Input**: "Create a task called 'Design review'"
- **Expected**: Confirmation, task created

- **Input**: "When is it due?"
- **Expected**: Asks for clarification since the task had no due date set
- **Test Result**: ✓ PASS / ✗ FAIL

#### 8.2 Multi-message Conversations
Create a 5+ message conversation and verify:
- Agent remembers context from previous messages
- Agent can reference earlier created tasks
- Agent maintains conversation coherence

- **Input 1**: "Create a project-related task"
- **Input 2**: "Add another task to the same project"
- **Input 3**: "Show me all tasks from that project"
- **Expected**: Agent recalls and correctly filters to project
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 9. UI/UX TESTS

#### 9.1 Message Display
- Verify user messages appear on the right side
- Verify assistant messages appear on the left side
- Check timestamps display correctly
- Verify emoji and special characters render properly
- Test message wrapping for long messages

#### 9.2 Loading States
- Send a message and verify loading spinner appears
- Verify spinner disappears when response arrives
- Check that message input is disabled during loading

#### 9.3 Input Field Behavior
- Verify input clears after sending
- Check that Enter key submits (but Shift+Enter should create new line)
- Verify character limits if any
- Test placeholder text in input

#### 9.4 Suggestion Buttons
- Click each suggestion button and verify:
  - Text populates input field
  - User can modify before sending
  - Focus returns to input field

#### 9.5 Scrolling Behavior
- Send multiple messages
- Verify auto-scroll to latest message
- Verify user can scroll up to see conversation history
- Check scroll performance with 20+ messages

---

### 10. ERROR HANDLING TESTS

#### 10.1 Network Errors
- Disconnect network and try to send message
- **Expected**: Error message displayed to user
- **Reconnect**: Retry should work
- **Test Result**: ✓ PASS / ✗ FAIL

#### 10.2 Server Errors
- Check backend logs for errors when intentionally causing issues
- **Expected**: Graceful error message shown to user, not raw error
- **Test Result**: ✓ PASS / ✗ FAIL

#### 10.3 Authentication Issues
- Open agent page without being logged in
- **Expected**: Redirect to login or show auth error
- **Test Result**: ✓ PASS / ✗ FAIL

---

### 11. PERFORMANCE TESTS

#### 11.1 Response Time
Measure agent response times for:
- Simple queries: < 2 seconds
- Complex breakdowns: < 5 seconds
- Batch operations: < 5 seconds

#### 11.2 High Volume Messages
Send 20 messages rapidly and verify:
- No messages lost
- No duplicate messages
- Correct order maintained

#### 11.3 Long Conversations
Send 50+ messages and verify:
- No performance degradation
- Memory not leaking
- Scrolling remains smooth

---

### 12. DARK MODE TESTS
- Toggle dark mode on and off
- Verify message colors are readable in both modes
- Check that message bubbles have proper contrast
- Verify timestamps are readable in both modes

---

## Test Execution Instructions

### Setup
1. Ensure backend is running: `python run_dev.py`
2. Ensure frontend is running: `npm run dev`
3. Navigate to `http://localhost:5173`
4. Log in with Firebase credentials
5. Click "AI Agent" in the sidebar

### For Each Test
1. Read the input instruction
2. Type the exact input (or similar phrasing)
3. Observe the response
4. Mark PASS or FAIL
5. Note any issues or unexpected behaviors
6. Take screenshots if needed

### Reporting Results
- Document all FAIL results with:
  - Input text
  - Expected behavior
  - Actual behavior
  - Screenshot (if applicable)
  - Any error messages from console

---

## Success Criteria

### MVP (Minimum Viable Product)
- ✓ Agent accepts and responds to messages
- ✓ Can create at least simple tasks
- ✓ Can list/query tasks
- ✓ Graceful error handling for invalid input

### Full Feature Completion
- ✓ All 5 agents (Supervisor, Planner, Executor, Query, Conversation) functional
- ✓ Multi-turn conversations with context
- ✓ Task CRUD operations working
- ✓ Complex planning and suggestions working
- ✓ 90%+ of test cases passing
- ✓ Response time < 5 seconds for 95% of requests
- ✓ Zero unhandled errors reaching user

---

## Known Limitations & Notes

1. **Initial State**: Agent starts with "Conversations: 1" (default greeting message)
2. **Tasks Created Counter**: Currently static at 0 (may be incremented by agent actions)
3. **Optional Features**: Full LLM integration (using fallback rule-based system)
4. **Memory**: Conversation history may be limited based on storage implementation

---

## Additional Testing URLs

- Agent Chat Endpoint: `POST /api/v1/agent/chat`
- Agent Capabilities: `GET /api/v1/agent/capabilities`
- Chat History: `GET /api/v1/agent/history`
- Clear History: `DELETE /api/v1/agent/history`

---

## Contact & Support

For test result issues or questions:
- Check backend logs: `python run_dev.py` output
- Check frontend console: Browser DevTools (F12) > Console
- Check API responses: Network tab in DevTools
