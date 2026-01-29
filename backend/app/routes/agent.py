"""
Agent routes for AI-powered task management with conversation support.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.dependencies import get_current_user
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentMessageRequest(BaseModel):
    """Request model for agent messages."""
    message: str
    conversation_id: Optional[str] = None  # If None, creates new conversation


class AgentMessageResponse(BaseModel):
    """Response model for agent messages."""
    type: str
    message: str
    conversation_id: str  # Return conversation ID
    task: Optional[dict] = None
    tasks: Optional[List[dict]] = None


class ConversationListItem(BaseModel):
    """Conversation item for list view."""
    id: str
    title: str
    message_count: int
    updated_at: str  # ISO timestamp
    archived: bool


class ConversationDetail(BaseModel):
    """Full conversation with all messages."""
    id: str
    title: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    archived: bool
    metadata: Dict[str, Any]


@router.post("/chat", response_model=AgentMessageResponse)
async def chat_with_agent(
    request: AgentMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AgentMessageResponse:
    """
    Chat with the LangGraph multi-agent system with conversation tracking.

    Creates a new conversation if conversation_id not provided.
    Maintains full context from previous messages in the conversation.

    The system uses 5 specialized agents:
    - Supervisor: Routes requests to appropriate agents
    - Planner: Breaks down complex projects
    - Executor: Creates/updates/deletes tasks
    - Query: Searches and filters tasks
    - Conversation: General help and Q&A

    Args:
        request: The user's message and optional conversation_id
        current_user: Authenticated user from dependency

    Returns:
        Agent's response with type, message, conversation_id, and optional task data
    """
    try:
        user_id = current_user["uid"]
        conversation_service = ConversationService(user_id)
        agent_service = AgentService(user_id)

        # Create conversation if not provided
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = conversation_service.create_conversation(
                initial_message=request.message
            )

        # Save user message to conversation
        conversation_service.add_message(
            conversation_id,
            role="user",
            content=request.message,
            metadata={"timestamp": str(__import__('datetime').datetime.utcnow())}
        )

        # Get conversation context for agent
        context = conversation_service.get_conversation_context(conversation_id, max_messages=10)

        # Process the message with context
        response = await agent_service.process_text_message(
            user_id=user_id,
            message=request.message,
            context=context
        )

        # Save assistant response to conversation
        conversation_service.add_message(
            conversation_id,
            role="assistant",
            content=response.get("message", ""),
            metadata={
                "type": response.get("type", "response"),
                "timestamp": str(__import__('datetime').datetime.utcnow())
            }
        )

        return AgentMessageResponse(
            type=response.get("type", "response"),
            message=response.get("message", ""),
            conversation_id=conversation_id,
            task=response.get("task"),
            tasks=response.get("tasks")
        )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Agent chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 50,
    archived: bool = False
):
    """
    List all conversations for the current user.

    Args:
        current_user: Authenticated user
        limit: Max conversations to return
        archived: Include archived conversations

    Returns:
        List of conversations with metadata (without full message list)
    """
    try:
        user_id = current_user["uid"]
        service = ConversationService(user_id)
        
        conversations = service.list_conversations(limit=limit, archived=archived)
        
        # Format for response
        return [
            ConversationListItem(
                id=conv["id"],
                title=conv.get("title", "Untitled"),
                message_count=conv.get("message_count", len(conv.get("messages", []))),
                updated_at=str(conv.get("updated_at", "")),
                archived=conv.get("archived", False)
            )
            for conv in conversations
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific conversation with all messages.

    Args:
        conversation_id: ID of the conversation
        current_user: Authenticated user

    Returns:
        Full conversation with all messages and metadata
    """
    try:
        user_id = current_user["uid"]
        service = ConversationService(user_id)
        
        conversation = service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return ConversationDetail(
            id=conversation["id"],
            title=conversation.get("title", "Untitled"),
            messages=conversation.get("messages", []),
            created_at=str(conversation.get("created_at", "")),
            updated_at=str(conversation.get("updated_at", "")),
            archived=conversation.get("archived", False),
            metadata=conversation.get("metadata", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@router.post("/conversations")
async def create_conversation(
    current_user: Dict[str, Any] = Depends(get_current_user),
    title: Optional[str] = None
):
    """
    Create a new conversation.

    Args:
        current_user: Authenticated user
        title: Optional conversation title

    Returns:
        Created conversation with ID
    """
    try:
        user_id = current_user["uid"]
        service = ConversationService(user_id)
        
        conversation_id = service.create_conversation(title=title)
        
        return {
            "id": conversation_id,
            "title": title or "New Conversation",
            "message_count": 0,
            "created_at": str(__import__('datetime').datetime.utcnow())
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.put("/conversations/{conversation_id}")
async def update_conversation_title(
    conversation_id: str,
    title: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update conversation title.

    Args:
        conversation_id: ID of the conversation
        title: New title
        current_user: Authenticated user

    Returns:
        Updated conversation
    """
    try:
        user_id = current_user["uid"]
        service = ConversationService(user_id)
        
        service.update_conversation_metadata(
            conversation_id,
            {"title": title}
        )
        
        return {"success": True, "message": "Conversation title updated"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    permanent: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete (archive or permanently) a conversation.

    Args:
        conversation_id: ID of the conversation
        permanent: If True, permanently delete; if False, archive
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        user_id = current_user["uid"]
        service = ConversationService(user_id)
        
        if permanent:
            service.delete_conversation(conversation_id)
        else:
            service.archive_conversation(conversation_id)
        
        action = "deleted" if permanent else "archived"
        return {"success": True, "message": f"Conversation {action}"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
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
