"""
Agent Conversation Tests for TaskTrail

Tests the multi-agent system with realistic conversation scenarios:
- Normal conversations
- Task creation conversations
- Project with tasks creation
- Query conversations (what should I do today, what's next)
- Complex multi-turn interactions

Usage:
    pytest tests/test_agent_conversations.py -v -s
"""

import pytest
pytest.skip("Deprecated in test cleanup. See docs/TESTING.md", allow_module_level=True)
import asyncio
import sys
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)



@pytest.fixture
def conversation_id():
    """Store conversation ID across tests."""
    return {"id": None}


class TestNormalConversations:
    """Test general conversation abilities."""

    def test_greeting(self, auth_headers):
        """Test agent responds to greetings."""
        message_data = {
            "message": "Hello! How are you?",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "conversation_id" in data
        assert data["type"] in ["response", "conversation"]
        print(f"\n🤖 Agent: {data['message']}")

    def test_capabilities_question(self, auth_headers):
        """Test asking what the agent can do."""
        message_data = {
            "message": "What can you help me with?",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 50  # Should give detailed response
        print(f"\n🤖 Agent: {data['message']}")

    def test_help_request(self, auth_headers):
        """Test asking for help."""
        message_data = {
            "message": "I need help organizing my tasks",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")


class TestTaskCreationConversations:
    """Test task creation through conversation."""

    def test_simple_task_creation(self, auth_headers):
        """Test creating a single task."""
        message_data = {
            "message": "Create a task: Review quarterly reports by Friday",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "task" in data or "tasks" in data
        print(f"\n🤖 Agent: {data['message']}")
        if data.get("task"):
            print(f"✅ Task created: {data['task']['title']}")

    def test_task_with_details(self, auth_headers):
        """Test creating task with multiple details."""
        message_data = {
            "message": "Create a high priority task to prepare presentation for Monday morning with description: Include Q4 metrics and growth projections",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")

    def test_multiple_tasks_creation(self, auth_headers):
        """Test creating multiple tasks at once."""
        message_data = {
            "message": "Create these tasks: 1) Email the team 2) Update documentation 3) Schedule code review",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        if data.get("tasks"):
            print(f"\n✅ Created {len(data['tasks'])} tasks")
        print(f"🤖 Agent: {data['message']}")


class TestProjectWithTasksConversations:
    """Test creating projects with associated tasks."""

    def test_project_creation_with_context(self, auth_headers, conversation_id):
        """Test creating a project and then tasks for it."""
        # Step 1: Create project
        message_data = {
            "message": "Create a project called 'Q1 Marketing Campaign' with description 'Launch new product marketing for Q1 2026'",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        conversation_id["id"] = data["conversation_id"]
        print(f"\n🤖 Agent: {data['message']}")
        
        # Give a moment for processing
        time.sleep(1)
        
        # Step 2: Create tasks for the project
        message_data = {
            "message": "Now create tasks for this project: Market research, Design campaign materials, Create social media content, Launch ads",
            "conversation_id": conversation_id["id"]
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"\n🤖 Agent: {data['message']}")

    def test_project_with_planning(self, auth_headers):
        """Test creating project and having AI plan the tasks."""
        # Ask for planning
        message_data = {
            "message": "I want to build a mobile app. Help me plan what tasks I need.",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        conv_id = data["conversation_id"]
        print(f"\n🤖 Agent Planning: {data['message'][:200]}...")
        
        time.sleep(1)
        
        # Create the tasks
        message_data = {
            "message": "Great! Please create all those tasks under a project called 'Mobile App Development'",
            "conversation_id": conv_id
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"\n🤖 Agent: {data['message']}")


class TestQueryConversations:
    """Test querying tasks and getting insights."""

    def test_what_should_i_do_today(self, auth_headers):
        """Test asking what to focus on today."""
        message_data = {
            "message": "What should I focus on today?",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")

    def test_whats_my_next_task(self, auth_headers):
        """Test asking for next task."""
        message_data = {
            "message": "What's my next task?",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")

    def test_show_high_priority_tasks(self, auth_headers):
        """Test querying high priority tasks."""
        message_data = {
            "message": "Show me all my high priority tasks",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")

    def test_whats_due_this_week(self, auth_headers):
        """Test asking about tasks due this week."""
        message_data = {
            "message": "What tasks are due this week?",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")

    def test_list_all_projects(self, auth_headers):
        """Test asking to see all projects."""
        message_data = {
            "message": "Show me all my projects",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")

    def test_task_count_query(self, auth_headers):
        """Test asking how many tasks exist."""
        message_data = {
            "message": "How many tasks do I have?",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"\n🤖 Agent: {data['message']}")


class TestConversationManagement:
    """Test conversation management endpoints."""

    def test_list_conversations(self, auth_headers):
        """Test listing all conversations."""
        response = client.get("/api/v1/agent/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"\n📝 Total conversations: {len(data)}")
        if data:
            print(f"   Latest: {data[0].get('title', 'Untitled')}")

    def test_get_specific_conversation(self, auth_headers):
        """Test retrieving a specific conversation."""
        # First get list of conversations
        response = client.get("/api/v1/agent/conversations", headers=auth_headers)
        conversations = response.json()
        
        if conversations:
            conv_id = conversations[0]["id"]
            response = client.get(f"/api/v1/agent/conversations/{conv_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            print(f"\n📖 Conversation has {len(data['messages'])} messages")


class TestComplexScenarios:
    """Test complex multi-turn conversations."""

    def test_full_workflow(self, auth_headers):
        """Test a complete workflow: project → tasks → query → update."""
        print("\n" + "="*60)
        print("TESTING FULL WORKFLOW")
        print("="*60)
        
        # Step 1: Create project
        print("\n📁 Step 1: Creating project...")
        message_data = {
            "message": "Create a project called 'Website Redesign' for redesigning our company website",
            "conversation_id": None
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        data = response.json()
        conv_id = data["conversation_id"]
        print(f"   {data['message'][:100]}...")
        time.sleep(1)
        
        # Step 2: Plan tasks
        print("\n📋 Step 2: Planning tasks...")
        message_data = {
            "message": "What tasks do we need for this website redesign?",
            "conversation_id": conv_id
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        data = response.json()
        print(f"   {data['message'][:200]}...")
        time.sleep(1)
        
        # Step 3: Create the tasks
        print("\n✅ Step 3: Creating tasks...")
        message_data = {
            "message": "Create all those tasks for the Website Redesign project",
            "conversation_id": conv_id
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        data = response.json()
        print(f"   {data['message'][:200]}...")
        time.sleep(1)
        
        # Step 4: Query the tasks
        print("\n🔍 Step 4: Querying tasks...")
        message_data = {
            "message": "Show me all tasks for the Website Redesign project",
            "conversation_id": conv_id
        }
        response = client.post("/api/v1/agent/chat", json=message_data, headers=auth_headers)
        data = response.json()
        print(f"   {data['message'][:200]}...")
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETE")
        print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
