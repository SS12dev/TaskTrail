"""
Agent State Models for LangGraph Multi-Agent System.

This module defines the state structure that flows through the LangGraph
multi-agent system, including conversation messages, user context, task context,
and agent coordination metadata.
"""

from typing import TypedDict, List, Optional, Literal, Annotated
from langgraph.graph.message import add_messages


class ConversationMessage(TypedDict):
    """Single message in a conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str  # ISO format


class TaskContext(TypedDict):
    """Context about the task being discussed."""
    task_id: Optional[str]
    title: Optional[str]
    description: Optional[str]
    priority: Optional[Literal["low", "medium", "high", "urgent"]]
    due_date: Optional[str]
    tags: List[str]
    project_id: Optional[str]
    subtasks: List[dict]  # For planner breakdown


class UserContext(TypedDict):
    """User-specific context."""
    user_id: str
    email: Optional[str]
    current_projects: List[str]
    task_count: int
    preferences: dict

from datetime import datetime




class AgentState(TypedDict):
    """
    Complete state flowing through LangGraph nodes.

    This state is passed between agents and accumulates information
    as the request is processed through the multi-agent system.
    """
    # Conversation (with special handling for message accumulation)
    messages: Annotated[List[ConversationMessage], add_messages]

    # Context
    user_context: UserContext
    task_context: TaskContext

    # Agent coordination
    current_intent: Optional[str]  # create|query|update|plan|conversation
    active_agent: Optional[str]  # Which agent is currently handling the request
    agents_called: List[str]  # Track which agents have been involved

    # Detailed user context
    detailed_user_context: Optional['DetailedUserContext']

    class DetailedUserContext(TypedDict):
        """Detailed user context with timezone and current time for AI agents."""
        current_timestamp: datetime
        timezone: str
        locale: str
        country: Optional[str]
        day_of_week: str
        time_of_day: str  # morning, afternoon, evening, night

    # Results & errors
    last_action: Optional[str]
    last_result: Optional[dict]
    error_message: Optional[str]

    # Loop control
    iteration_count: int  # Prevent infinite loops
