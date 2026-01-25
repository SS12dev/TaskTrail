"""
TaskTrail Agent Card Generator

Generates and serves TaskTrail's Agent Card for A2A agent discovery.
The Agent Card is served at /.well-known/agent-card.json
"""

from typing import Optional
from app.models.a2a_models import (
    AgentCard,
    AgentCapability,
    SecurityScheme,
    RateLimit,
)
from app.config import get_settings


def generate_agent_card(
    base_url: Optional[str] = None,
) -> AgentCard:
    """
    Generate TaskTrail's Agent Card for A2A discovery

    Args:
        base_url: Optional base URL override (useful for dynamic configuration)

    Returns:
        AgentCard describing TaskTrail's capabilities
    """
    settings = get_settings()

    # Use provided base_url or fall back to config
    service_endpoint = base_url or settings.a2a_service_endpoint

    # Define TaskTrail's capabilities
    capabilities = [
        AgentCapability(
            id="create_task",
            name="Create Task",
            description="Create and track new tasks with titles, descriptions, priorities, due dates, and tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Task priority level"
                    },
                    "due_date": {"type": "string", "format": "date", "description": "Due date (YYYY-MM-DD)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Task tags"},
                    "project_id": {"type": "string", "description": "Associated project ID"}
                },
                "required": ["title"]
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Created task ID"},
                    "status": {"type": "string", "description": "Creation status"}
                }
            },
            examples=[
                "Create a task to review the project proposal by Friday",
                "Add a high priority task: Fix login bug with authentication",
                "Create task: Schedule team meeting for next week"
            ]
        ),
        AgentCapability(
            id="query_tasks",
            name="Query Tasks",
            description="Search and filter tasks by status, priority, tags, projects, or date ranges",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "archived"],
                        "description": "Filter by task status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Filter by priority"
                    },
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                    "project_id": {"type": "string", "description": "Filter by project"},
                    "due_date_start": {"type": "string", "format": "date"},
                    "due_date_end": {"type": "string", "format": "date"}
                }
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "tasks": {"type": "array", "description": "Matching tasks"},
                    "count": {"type": "integer", "description": "Number of tasks found"}
                }
            },
            examples=[
                "Show me all high priority tasks",
                "What tasks are due this week?",
                "List pending tasks tagged with 'frontend'",
                "Find all tasks in the Mobile App project"
            ]
        ),
        AgentCapability(
            id="update_task",
            name="Update Task",
            description="Modify existing tasks: change status, priority, due dates, add notes, or update details",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to update"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "archived"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                    "due_date": {"type": "string", "format": "date"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string", "description": "Add notes to task"}
                },
                "required": ["task_id"]
            },
            examples=[
                "Mark task #123 as completed",
                "Change priority of bug fix task to urgent",
                "Update the due date to next Friday",
                "Add note: Waiting for client feedback"
            ]
        ),
        AgentCapability(
            id="plan_project",
            name="Plan Project",
            description="Break down complex projects into actionable subtasks with dependencies and timelines",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Project name"},
                    "description": {"type": "string", "description": "Project description"},
                    "goals": {"type": "array", "items": {"type": "string"}, "description": "Project goals"},
                    "constraints": {"type": "array", "items": {"type": "string"}, "description": "Constraints or requirements"}
                },
                "required": ["project_name", "description"]
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "subtasks": {"type": "array", "description": "Generated subtasks with dependencies"},
                    "timeline": {"type": "string", "description": "Suggested timeline"}
                }
            },
            examples=[
                "Plan a project to redesign the company website",
                "Break down the mobile app development into tasks",
                "Create a plan for the Q1 marketing campaign"
            ]
        ),
        AgentCapability(
            id="conversation",
            name="General Conversation",
            description="Natural language conversation about tasks, productivity tips, and project management advice",
            examples=[
                "What's the best way to organize my tasks?",
                "How should I prioritize competing deadlines?",
                "Give me tips for staying productive",
                "Explain the difference between urgent and important tasks"
            ]
        ),
    ]

    # Define security schemes
    security_schemes = {
        "firebase": SecurityScheme(
            type="bearer",
            scheme="bearer",
            bearerFormat="JWT",
            description="Firebase Authentication JWT token. Obtain from Firebase Auth and pass in Authorization header."
        ),
        "apiKey": SecurityScheme(
            type="apiKey",
            name="X-API-Key",
            in_="header",
            description="API key authentication (if configured). Contact TaskTrail admin for API key."
        ),
    }

    # Define rate limits
    rate_limits = [
        RateLimit(
            requests=60,
            period="minute",
            description="60 requests per minute per user"
        ),
        RateLimit(
            requests=1000,
            period="hour",
            description="1000 requests per hour per user"
        ),
    ]

    # Generate the Agent Card
    return AgentCard(
        agentId=settings.a2a_agent_id,
        name=settings.a2a_agent_name,
        description=(
            "TaskTrail is an intelligent multi-agent task management system powered by LangGraph. "
            "It uses specialized AI agents to help you create, organize, query, and plan tasks efficiently. "
            "The system includes a Supervisor agent for routing, specialized agents for task creation, "
            "querying, planning, and execution, plus a conversational agent for natural interactions."
        ),
        version="1.0.0",
        capabilities=capabilities,
        serviceEndpoint=service_endpoint,
        securitySchemes=security_schemes,
        rateLimits=rate_limits,
        metadata={
            "multi_agent_system": True,
            "streaming_support": True,
            "websocket_enabled": settings.websocket_enabled,
            "agents": [
                "Supervisor Agent (routing)",
                "Task Creator Agent",
                "Query Agent",
                "Planner Agent",
                "Executor Agent",
                "Conversation Agent"
            ],
            "powered_by": "LangGraph + LangChain + Firebase",
            "supported_formats": ["text", "structured_data"],
        }
    )


def get_capability_description(capability_id: str) -> Optional[str]:
    """
    Get human-readable description for a capability

    Args:
        capability_id: Capability identifier

    Returns:
        Capability description or None if not found
    """
    card = generate_agent_card()
    for capability in card.capabilities:
        if capability.id == capability_id:
            return capability.description
    return None


def supports_capability(capability_id: str) -> bool:
    """
    Check if TaskTrail supports a specific capability

    Args:
        capability_id: Capability identifier to check

    Returns:
        True if capability is supported
    """
    card = generate_agent_card()
    return any(cap.id == capability_id for cap in card.capabilities)
