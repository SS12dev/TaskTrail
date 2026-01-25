"""
Agent API endpoints for AI-powered task management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.core.auth import get_current_user
from app.services.agent_service import AgentService
from app.repositories.task_repository import TaskRepository
from app.core.firebase import db

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentMessageRequest(BaseModel):
    """Request model for agent messages."""
    message: str


class AgentMessageResponse(BaseModel):
    """Response model for agent messages."""
    type: str
    message: str
    task: Optional[dict] = None
    tasks: Optional[list] = None


@router.post("/chat", response_model=AgentMessageResponse)
async def chat_with_agent(
    request: AgentMessageRequest,
    current_user: dict = Depends(get_current_user)
) -> AgentMessageResponse:
    """
    Chat with the AI agent.

    The agent can:
    - Create tasks from natural language
    - Query and search tasks
    - Update and delete tasks
    - Provide suggestions and recommendations
    - Break down complex tasks
    """
    try:
        # Initialize services
        task_repository = TaskRepository(db)
        agent_service = AgentService(task_repository)

        # Process the message
        response = await agent_service.process_message(
            user_id=current_user["uid"],
            message=request.message
        )

        return AgentMessageResponse(**response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/capabilities")
async def get_agent_capabilities(
    current_user: dict = Depends(get_current_user)
):
    """
    Get information about the agent's capabilities.
    """
    return {
        "capabilities": [
            {
                "name": "Task Creation",
                "description": "Create tasks from natural language",
                "examples": [
                    "Create a task to finish the report by Friday",
                    "Add a high priority task for the team meeting",
                    "New task: Buy groceries tomorrow"
                ]
            },
            {
                "name": "Task Queries",
                "description": "Search and list tasks",
                "examples": [
                    "Show me my tasks for today",
                    "What are my high priority tasks?",
                    "List all overdue tasks"
                ]
            },
            {
                "name": "Task Updates",
                "description": "Update existing tasks",
                "examples": [
                    "Change task 'Report' priority to high",
                    "Update due date of 'Meeting prep' to tomorrow",
                    "Mark 'Review code' as complete"
                ]
            },
            {
                "name": "Smart Suggestions",
                "description": "Get AI-powered recommendations",
                "examples": [
                    "What should I focus on today?",
                    "Suggest how to organize my tasks",
                    "Give me productivity tips"
                ]
            },
            {
                "name": "Task Breakdown",
                "description": "Split complex tasks into subtasks",
                "examples": [
                    "Break down 'Launch product' into steps",
                    "How can I divide this project?",
                    "Split this task into smaller pieces"
                ]
            }
        ],
        "status": "active",
        "version": "1.0.0"
    }


@router.get("/history")
async def get_chat_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    Get chat history for the current user.

    TODO: Implement chat history storage and retrieval.
    """
    return {
        "messages": [],
        "total": 0,
        "message": "Chat history coming soon!"
    }
