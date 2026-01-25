"""
A2A (Agent-to-Agent) Protocol Server Routes

Implements A2A protocol endpoints for TaskTrail:
- Agent discovery (Agent Card)
- Message processing
- WebSocket streaming
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query
from fastapi.responses import JSONResponse
from firebase_admin import auth
from typing import Dict, Any, Optional
import logging

from app.dependencies import get_current_user
from app.models.a2a_models import A2AMessage, A2AResponse, TaskState
from app.a2a.agent_card import generate_agent_card
from app.a2a.adapters import A2AAdapter
from app.services.agent_service import AgentService
from app.firebase import get_firestore_client
from app.config import get_settings

logger = logging.getLogger(__name__)

# Create router without prefix - A2A endpoints use specific paths
router = APIRouter(tags=["A2A Protocol"])


# ============================================================================
# Agent Discovery
# ============================================================================

@router.get("/.well-known/agent-card.json")
async def get_agent_card():
    """
    A2A Agent Card Discovery Endpoint

    Returns TaskTrail's Agent Card describing capabilities, authentication,
    and service endpoints. This is the standard A2A discovery mechanism.

    Returns:
        AgentCard JSON describing TaskTrail's capabilities
    """
    settings = get_settings()

    if not settings.a2a_enable_server:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A2A server is disabled"
        )

    try:
        agent_card = generate_agent_card()
        logger.info("Agent card requested")
        return JSONResponse(content=agent_card.model_dump())
    except Exception as e:
        logger.error(f"Error generating agent card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate agent card"
        )


# ============================================================================
# A2A Message Processing
# ============================================================================

@router.post("/a2a/v1/messages", response_model=A2AResponse)
async def process_a2a_message(
    message: A2AMessage,
    user: Dict[str, Any] = Depends(get_current_user),
) -> A2AResponse:
    """
    Process an incoming A2A protocol message

    This endpoint receives A2A-formatted messages, converts them to TaskTrail's
    internal format, processes them through the multi-agent system, and returns
    an A2A-formatted response.

    Args:
        message: A2A protocol message
        user: Authenticated user from Firebase token

    Returns:
        A2A protocol response with task state and results
    """
    settings = get_settings()

    if not settings.a2a_enable_server:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A2A server is disabled"
        )

    logger.info(
        f"A2A message received - contextId: {message.contextId}, "
        f"taskId: {message.taskId}, role: {message.role}"
    )

    try:
        # Get or create agent service for user
        agent_service = AgentService.get_instance(user["uid"])

        # Get user context from Firestore
        db = get_firestore_client()
        user_doc = db.collection("users").document(user["uid"]).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        user_context = {
            "user_id": user["uid"],
            "email": user.get("email"),
            "current_projects": user_data.get("projects", []),
            "task_count": user_data.get("task_count", 0),
            "preferences": user_data.get("preferences", {}),
        }

        # Convert A2A message to AgentState
        agent_state = A2AAdapter.a2a_to_agent_state(
            a2a_message=message,
            user_id=user["uid"],
            user_context=user_context,
        )

        # Process through multi-agent system
        result_state = await agent_service.process_message(agent_state)

        # Convert result back to A2A format
        task_id = message.taskId or f"task-{message.messageId}"

        # Determine task state based on result
        if result_state.get("error_message"):
            task_state = TaskState.FAILED
        else:
            task_state = TaskState.COMPLETED

        a2a_response = A2AAdapter.agent_state_to_a2a(
            state=result_state,
            context_id=message.contextId,
            task_id=task_id,
            task_state=task_state,
        )

        logger.info(
            f"A2A message processed successfully - taskId: {task_id}, "
            f"state: {task_state}"
        )

        return a2a_response

    except Exception as e:
        logger.error(f"Error processing A2A message: {e}", exc_info=True)

        # Return error response in A2A format
        error_response = A2AAdapter.create_error_response(
            context_id=message.contextId,
            task_id=message.taskId or f"task-{message.messageId}",
            error_message=str(e),
            error_code="PROCESSING_ERROR",
        )

        return error_response


# ============================================================================
# WebSocket Streaming
# ============================================================================

async def verify_websocket_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase token for WebSocket connection

    Args:
        token: Firebase JWT token

    Returns:
        Decoded token data

    Raises:
        ValueError: If token is invalid
    """
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        return decoded_token
    except Exception as e:
        logger.error(f"WebSocket token verification failed: {e}")
        raise ValueError("Invalid authentication token")


@router.websocket("/a2a/v1/ws/{context_id}")
async def websocket_a2a_endpoint(
    websocket: WebSocket,
    context_id: str,
    token: str = Query(..., description="Firebase authentication token"),
):
    """
    WebSocket endpoint for streaming A2A task updates

    Provides real-time updates during task processing:
    - State changes (submitted → working → completed)
    - Partial output chunks
    - Agent switches
    - Error notifications

    Args:
        websocket: WebSocket connection
        context_id: A2A context identifier
        token: Firebase JWT token for authentication

    WebSocket Message Format:
        {
            "type": "state_change|output_chunk|error|task_complete|agent_switch",
            "contextId": "context-uuid",
            "taskId": "task-uuid",
            "data": {...},
            "timestamp": "2025-01-13T10:30:00Z"
        }
    """
    settings = get_settings()

    if not settings.websocket_enabled:
        await websocket.close(code=1003, reason="WebSocket support is disabled")
        return

    # Authenticate WebSocket connection
    try:
        user_data = await verify_websocket_token(token)
        user_id = user_data["uid"]
        logger.info(f"WebSocket connection authenticated for user: {user_id}")
    except ValueError as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Accept WebSocket connection
    await websocket.accept()
    logger.info(f"WebSocket connected - contextId: {context_id}, user: {user_id}")

    try:
        # Import WebSocket manager here to avoid circular imports
        from app.a2a.websocket_manager import manager

        # Register connection
        await manager.connect(websocket, context_id, user_id)

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "contextId": context_id,
            "message": "WebSocket connection established",
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})

                elif message_type == "message":
                    # Process incoming A2A message via WebSocket
                    try:
                        a2a_message = A2AMessage(**data.get("message", {}))

                        # Get agent service
                        agent_service = AgentService.get_instance(user_id)

                        # Get user context
                        db = get_firestore_client()
                        user_doc = db.collection("users").document(user_id).get()
                        user_data_dict = user_doc.to_dict() if user_doc.exists else {}

                        user_context = {
                            "user_id": user_id,
                            "email": user_data.get("email"),
                            "current_projects": user_data_dict.get("projects", []),
                            "task_count": user_data_dict.get("task_count", 0),
                            "preferences": user_data_dict.get("preferences", {}),
                        }

                        # Convert and process
                        agent_state = A2AAdapter.a2a_to_agent_state(
                            a2a_message=a2a_message,
                            user_id=user_id,
                            user_context=user_context,
                        )

                        # Process with streaming updates
                        task_id = a2a_message.taskId or f"task-{a2a_message.messageId}"

                        # Send working state
                        await manager.send_update(
                            context_id,
                            {
                                "type": "state_change",
                                "contextId": context_id,
                                "taskId": task_id,
                                "data": {
                                    "taskState": TaskState.WORKING.value,
                                    "message": "Processing your request...",
                                },
                            }
                        )

                        # Process message
                        result_state = await agent_service.process_message(agent_state)

                        # Determine final state
                        if result_state.get("error_message"):
                            final_state = TaskState.FAILED
                        else:
                            final_state = TaskState.COMPLETED

                        # Convert to A2A response
                        a2a_response = A2AAdapter.agent_state_to_a2a(
                            state=result_state,
                            context_id=context_id,
                            task_id=task_id,
                            task_state=final_state,
                        )

                        # Send completion
                        await manager.send_update(
                            context_id,
                            {
                                "type": "task_complete",
                                "contextId": context_id,
                                "taskId": task_id,
                                "data": {
                                    "response": a2a_response.model_dump(),
                                },
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
                        await manager.send_update(
                            context_id,
                            {
                                "type": "error",
                                "contextId": context_id,
                                "data": {
                                    "error": str(e),
                                },
                            }
                        )

                elif message_type == "cancel":
                    # Handle task cancellation
                    task_id = data.get("taskId")
                    logger.info(f"Task cancellation requested: {task_id}")
                    await websocket.send_json({
                        "type": "cancelled",
                        "contextId": context_id,
                        "taskId": task_id,
                        "message": "Task cancellation requested",
                    })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected - contextId: {context_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)
                break

    finally:
        # Cleanup connection
        await manager.disconnect(websocket, context_id)
        logger.info(f"WebSocket connection closed - contextId: {context_id}")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/a2a/v1/health")
async def a2a_health_check():
    """
    A2A service health check

    Returns:
        Health status of A2A service
    """
    settings = get_settings()

    return {
        "status": "healthy",
        "a2a_server_enabled": settings.a2a_enable_server,
        "a2a_client_enabled": settings.a2a_enable_client,
        "websocket_enabled": settings.websocket_enabled,
        "agent_id": settings.a2a_agent_id,
    }
