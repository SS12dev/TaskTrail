"""
Agent routes for AI-powered task management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.dependencies import get_current_user
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentMessageRequest(BaseModel):
    """Request model for agent messages."""
    message: str


class AgentMessageResponse(BaseModel):
    """Response model for agent messages."""
    type: str
    message: str
    task: Optional[dict] = None
    tasks: Optional[List[dict]] = None


@router.post("/chat", response_model=AgentMessageResponse)
async def chat_with_agent(
    request: AgentMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AgentMessageResponse:
    """
    Chat with the LangGraph multi-agent system.

    The system uses 5 specialized agents:
    - Supervisor: Routes requests to appropriate agents
    - Planner: Breaks down complex projects
    - Executor: Creates/updates/deletes tasks
    - Query: Searches and filters tasks
    - Conversation: General help and Q&A

    Args:
        request: The user's message
        current_user: Authenticated user from dependency

    Returns:
        Agent's response with type, message, and optional task data
    """
    try:
        user_id = current_user["uid"]

        # Initialize agent service for this user
        agent_service = AgentService(user_id)

        # Process the message
        response = await agent_service.process_text_message(
            user_id=user_id,
            message=request.message
        )

        return AgentMessageResponse(**response)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Agent chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/capabilities")
async def get_agent_capabilities(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get information about the agent's capabilities.

    Returns comprehensive list of what the AI agent can do,
    with examples for each capability.
    """
    return {
        "capabilities": [
            {
                "name": "Task Creation",
                "description": "Create tasks from natural language",
                "icon": "plus-circle",
                "examples": [
                    "Create a task to finish the report by Friday",
                    "Add a high priority task for the team meeting",
                    "New task: Buy groceries tomorrow"
                ]
            },
            {
                "name": "Task Queries",
                "description": "Search and list tasks",
                "icon": "search",
                "examples": [
                    "Show me my tasks for today",
                    "What are my high priority tasks?",
                    "List all overdue tasks",
                    "What's on my calendar this week?"
                ]
            },
            {
                "name": "Task Updates",
                "description": "Update existing tasks",
                "icon": "edit",
                "examples": [
                    "Change task 'Report' priority to high",
                    "Update due date of 'Meeting prep' to tomorrow",
                    "Mark 'Review code' as complete"
                ]
            },
            {
                "name": "Smart Suggestions",
                "description": "Get AI-powered recommendations",
                "icon": "lightbulb",
                "examples": [
                    "What should I focus on today?",
                    "Suggest how to organize my tasks",
                    "Give me productivity tips",
                    "Help me prioritize my work"
                ]
            },
            {
                "name": "Task Breakdown",
                "description": "Split complex tasks into subtasks",
                "icon": "list",
                "examples": [
                    "Break down 'Launch product' into steps",
                    "How can I divide this project?",
                    "Split 'Website redesign' into smaller tasks"
                ]
            }
        ],
        "status": "active",
        "version": "1.0.0",
        "model": "rule-based (LLM integration coming soon)"
    }


@router.get("/history")
async def get_chat_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 50
):
    """
    Get chat history for the current user.

    Args:
        current_user: Authenticated user
        limit: Maximum number of messages to return

    Returns:
        List of previous chat messages
    """
    from app.services.conversation_memory import ConversationMemory

    user_id = current_user["uid"]
    memory = ConversationMemory(user_id)

    history = memory.get_recent_history(limit)

    return {
        "messages": history,
        "total": len(history),
        "has_more": len(history) >= limit
    }


@router.delete("/history")
async def clear_chat_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Clear chat history for the current user.

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    from app.services.conversation_memory import ConversationMemory

    user_id = current_user["uid"]
    memory = ConversationMemory(user_id)

    memory.clear_history()

    # Also clear agent system cache
    AgentService.clear_cache(user_id)

    return {
        "success": True,
        "message": "Chat history cleared successfully"
    }
