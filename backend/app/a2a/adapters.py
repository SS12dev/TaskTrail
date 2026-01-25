"""
A2A Protocol Adapters

Bidirectional conversion between A2A protocol format and TaskTrail's internal AgentState format.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
import logging

from app.models.a2a_models import (
    A2AMessage,
    A2AResponse,
    TaskState,
    TaskUpdate,
)
from app.models.agent_state import (
    AgentState,
    ConversationMessage,
    UserContext,
    TaskContext,
)

logger = logging.getLogger(__name__)


class A2AAdapter:
    """Adapter for converting between A2A and TaskTrail formats"""

    @staticmethod
    def a2a_to_agent_state(
        a2a_message: A2AMessage,
        user_id: str,
        user_context: Optional[UserContext] = None,
        existing_state: Optional[AgentState] = None,
    ) -> AgentState:
        """
        Convert A2A message to TaskTrail AgentState

        Args:
            a2a_message: Incoming A2A protocol message
            user_id: User identifier
            user_context: Optional user context (if None, creates minimal context)
            existing_state: Optional existing state to build upon

        Returns:
            AgentState ready for LangGraph processing
        """
        # Extract text content from A2A message parts
        text_content = a2a_message.get_text_content()

        # Create conversation message
        conversation_message: ConversationMessage = {
            "role": a2a_message.role,
            "content": text_content,
            "timestamp": a2a_message.timestamp.isoformat(),
        }

        # Use existing state or create new state
        if existing_state:
            # Append to existing messages
            state = existing_state.copy()
            state["messages"].append(conversation_message)
            state["iteration_count"] += 1
        else:
            # Create new state
            state: AgentState = {
                "messages": [conversation_message],
                "user_context": user_context or {
                    "user_id": user_id,
                    "email": None,
                    "current_projects": [],
                    "task_count": 0,
                    "preferences": {},
                },
                "task_context": {
                    "task_id": a2a_message.taskId,
                    "title": None,
                    "description": None,
                    "priority": None,
                    "due_date": None,
                    "tags": [],
                    "project_id": None,
                    "subtasks": [],
                },
                "current_intent": None,
                "active_agent": None,
                "agents_called": [],
                "last_action": None,
                "last_result": None,
                "error_message": None,
                "iteration_count": 0,
            }

        # Extract structured data from A2A message if available
        data_parts = a2a_message.get_data_content()
        for data in data_parts:
            # Check for task-related structured data
            if "task" in data:
                task_data = data["task"]
                if "title" in task_data:
                    state["task_context"]["title"] = task_data["title"]
                if "description" in task_data:
                    state["task_context"]["description"] = task_data["description"]
                if "priority" in task_data:
                    state["task_context"]["priority"] = task_data["priority"]
                if "due_date" in task_data:
                    state["task_context"]["due_date"] = task_data["due_date"]
                if "tags" in task_data:
                    state["task_context"]["tags"] = task_data["tags"]
                if "project_id" in task_data:
                    state["task_context"]["project_id"] = task_data["project_id"]

            # Check for intent hints
            if "intent" in data:
                state["current_intent"] = data["intent"]

        # Store A2A metadata for context tracking
        if a2a_message.metadata:
            state["last_result"] = {
                "a2a_context_id": a2a_message.contextId,
                "a2a_message_id": a2a_message.messageId,
                "a2a_metadata": a2a_message.metadata,
            }

        return state

    @staticmethod
    def agent_state_to_a2a(
        state: AgentState,
        context_id: str,
        task_id: Optional[str] = None,
        task_state: TaskState = TaskState.COMPLETED,
    ) -> A2AResponse:
        """
        Convert TaskTrail AgentState to A2A response

        Args:
            state: Current AgentState after processing
            context_id: A2A context identifier
            task_id: Optional task identifier (generates new if None)
            task_state: Task execution state

        Returns:
            A2A protocol response
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = f"task-{uuid4()}"

        # Extract assistant's response from messages (handle both dict and LangChain objects)
        logger.debug(f"Converting AgentState to A2A - Messages count: {len(state.get('messages', []))}")

        assistant_messages = []
        for msg in state.get("messages", []):
            # Handle LangChain message objects
            if hasattr(msg, 'type'):
                if msg.type == 'ai':
                    assistant_messages.append({"content": msg.content})
            # Handle dict format
            elif isinstance(msg, dict):
                if msg.get("role") == "assistant":
                    assistant_messages.append(msg)

        # Get the most recent assistant message as response
        response_text = ""
        if assistant_messages:
            response_text = assistant_messages[-1]["content"]
            logger.info(f"A2A response extracted: {response_text[:100]}...")
        elif state.get("error_message"):
            response_text = f"Error: {state['error_message']}"
            task_state = TaskState.FAILED
            logger.warning(f"A2A error response: {response_text}")

        # Build response parts
        parts: List[Dict[str, Any]] = [
            {"text": response_text}
        ]

        # Add structured data if available
        if state.get("last_result"):
            result_data = state["last_result"]
            # Filter out A2A metadata to avoid circular references
            clean_result = {
                k: v for k, v in result_data.items()
                if not k.startswith("a2a_")
            }
            if clean_result:
                parts.append({"data": clean_result})

        # Build metadata
        metadata = {
            "agents_used": state.get("agents_called", []),
            "active_agent": state.get("active_agent"),
            "iteration_count": state.get("iteration_count", 0),
            "intent": state.get("current_intent"),
        }

        # Add task context if meaningful
        task_context = state.get("task_context", {})
        if task_context.get("task_id"):
            metadata["task"] = {
                "task_id": task_context.get("task_id"),
                "title": task_context.get("title"),
                "priority": task_context.get("priority"),
            }

        return A2AResponse(
            messageId=f"msg-{uuid4()}",
            contextId=context_id,
            taskId=task_id,
            taskState=task_state,
            role="assistant",
            parts=parts,
            metadata=metadata,
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def create_task_update(
        task_id: str,
        context_id: str,
        task_state: TaskState,
        message: Optional[str] = None,
        progress: Optional[float] = None,
        agent_name: Optional[str] = None,
    ) -> TaskUpdate:
        """
        Create a task status update for streaming

        Args:
            task_id: Task identifier
            context_id: Context identifier
            task_state: Current task state
            message: Optional status message
            progress: Optional progress percentage (0.0-1.0)
            agent_name: Optional name of active agent

        Returns:
            TaskUpdate for WebSocket streaming
        """
        metadata = {}
        if agent_name:
            metadata["active_agent"] = agent_name

        return TaskUpdate(
            taskId=task_id,
            contextId=context_id,
            taskState=task_state,
            message=message,
            progress=progress,
            metadata=metadata if metadata else None,
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def extract_user_message(a2a_message: A2AMessage) -> str:
        """
        Extract user message text from A2A message

        Simple helper to get just the text content for logging/display

        Args:
            a2a_message: A2A protocol message

        Returns:
            Extracted text content
        """
        return a2a_message.get_text_content()

    @staticmethod
    def create_error_response(
        context_id: str,
        task_id: str,
        error_message: str,
        error_code: Optional[str] = None,
    ) -> A2AResponse:
        """
        Create an A2A error response

        Args:
            context_id: Context identifier
            task_id: Task identifier
            error_message: Error description
            error_code: Optional error code

        Returns:
            A2A response with error state
        """
        parts = [
            {"text": f"An error occurred: {error_message}"}
        ]

        metadata = {
            "error": True,
            "error_message": error_message,
        }

        if error_code:
            metadata["error_code"] = error_code

        return A2AResponse(
            messageId=f"msg-{uuid4()}",
            contextId=context_id,
            taskId=task_id,
            taskState=TaskState.FAILED,
            role="system",
            parts=parts,
            metadata=metadata,
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def create_input_required_response(
        context_id: str,
        task_id: str,
        prompt: str,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> A2AResponse:
        """
        Create an A2A response requesting user input

        Args:
            context_id: Context identifier
            task_id: Task identifier
            prompt: Input prompt for the user
            input_schema: Optional JSON schema for expected input

        Returns:
            A2A response with input-required state
        """
        parts = [
            {"text": prompt}
        ]

        metadata = {
            "input_required": True,
        }

        if input_schema:
            metadata["input_schema"] = input_schema

        return A2AResponse(
            messageId=f"msg-{uuid4()}",
            contextId=context_id,
            taskId=task_id,
            taskState=TaskState.INPUT_REQUIRED,
            role="system",
            parts=parts,
            metadata=metadata,
            timestamp=datetime.utcnow(),
        )
