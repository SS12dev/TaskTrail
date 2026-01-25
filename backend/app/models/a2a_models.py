"""
A2A (Agent-to-Agent) Protocol Data Models

Based on Google/Linux Foundation A2A Protocol specification.
Defines standard message formats for agent interoperability.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from uuid import uuid4


# ============================================================================
# Message Parts
# ============================================================================

class TextPart(BaseModel):
    """Text content part of an A2A message"""
    text: str


class FilePart(BaseModel):
    """File attachment part of an A2A message"""
    file: Dict[str, str] = Field(
        ...,
        description="File metadata with 'uri' and 'mediaType' keys"
    )

    @property
    def uri(self) -> str:
        return self.file.get("uri", "")

    @property
    def media_type(self) -> str:
        return self.file.get("mediaType", "application/octet-stream")


class DataPart(BaseModel):
    """Structured data part of an A2A message"""
    data: Dict[str, Any]


# Union type for all message parts
MessagePart = Union[TextPart, FilePart, DataPart]


# ============================================================================
# Task State
# ============================================================================

class TaskState(str, Enum):
    """A2A task execution states"""
    SUBMITTED = "submitted"      # Task received, queued for processing
    WORKING = "working"          # Task being actively processed
    COMPLETED = "completed"      # Task completed successfully
    FAILED = "failed"            # Task failed with error
    CANCELLED = "cancelled"      # Task cancelled by user
    INPUT_REQUIRED = "input-required"  # Task waiting for user input
    REJECTED = "rejected"        # Task rejected (invalid, unauthorized, etc.)
    AUTH_REQUIRED = "auth-required"    # Task requires authentication


# ============================================================================
# A2A Messages
# ============================================================================

class A2AMessage(BaseModel):
    """
    A2A Protocol message format for agent communication

    Attributes:
        messageId: Unique identifier for this message
        contextId: Conversation/session context identifier
        taskId: Optional task identifier for tracking async operations
        role: Message role (user, assistant, system)
        parts: List of message content parts (text, file, data)
        metadata: Optional additional metadata
        timestamp: Message creation timestamp
    """
    messageId: str = Field(default_factory=lambda: f"msg-{uuid4()}")
    contextId: str
    taskId: Optional[str] = None
    role: Literal["user", "assistant", "system"]
    parts: List[Dict[str, Any]]  # Will be parsed as MessagePart union
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def get_text_content(self) -> str:
        """Extract all text content from message parts"""
        texts = []
        for part in self.parts:
            if "text" in part:
                texts.append(part["text"])
        return " ".join(texts)

    def get_data_content(self) -> List[Dict[str, Any]]:
        """Extract all structured data from message parts"""
        data_parts = []
        for part in self.parts:
            if "data" in part:
                data_parts.append(part["data"])
        return data_parts

    def get_file_attachments(self) -> List[Dict[str, str]]:
        """Extract all file attachments from message parts"""
        files = []
        for part in self.parts:
            if "file" in part:
                files.append(part["file"])
        return files


class A2AResponse(BaseModel):
    """
    A2A Protocol response format

    Attributes:
        messageId: Response message identifier
        contextId: Conversation context
        taskId: Associated task identifier
        taskState: Current task execution state
        role: Response role (typically 'assistant')
        parts: Response content parts
        metadata: Optional metadata (agent used, timing, etc.)
        timestamp: Response creation timestamp
    """
    messageId: str = Field(default_factory=lambda: f"msg-{uuid4()}")
    contextId: str
    taskId: str
    taskState: TaskState
    role: Literal["assistant", "system"] = "assistant"
    parts: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Task Management
# ============================================================================

class TaskUpdate(BaseModel):
    """Real-time task status update for streaming"""
    taskId: str
    contextId: str
    taskState: TaskState
    message: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskCancellation(BaseModel):
    """Request to cancel a running task"""
    taskId: str
    contextId: str
    reason: Optional[str] = None


# ============================================================================
# Agent Discovery (Agent Card)
# ============================================================================

class AgentCapability(BaseModel):
    """Describes a capability/skill the agent provides"""
    id: str
    name: str
    description: str
    inputSchema: Optional[Dict[str, Any]] = None
    outputSchema: Optional[Dict[str, Any]] = None
    examples: Optional[List[str]] = None


class SecurityScheme(BaseModel):
    """Authentication/security scheme supported by agent"""
    type: Literal["apiKey", "bearer", "oauth2", "none"]
    description: Optional[str] = None
    name: Optional[str] = None  # For apiKey: header/query param name
    in_: Optional[Literal["header", "query", "cookie"]] = Field(None, alias="in")
    scheme: Optional[str] = None  # For bearer: "bearer" or custom
    bearerFormat: Optional[str] = None  # E.g., "JWT"


class RateLimit(BaseModel):
    """Rate limiting information"""
    requests: int
    period: str  # E.g., "minute", "hour", "day"
    description: Optional[str] = None


class AgentCard(BaseModel):
    """
    A2A Agent Card for agent discovery

    Served at /.well-known/agent-card.json
    Describes agent capabilities, authentication, and service endpoint
    """
    agentId: str
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[AgentCapability]
    serviceEndpoint: str
    securitySchemes: Dict[str, SecurityScheme]
    rateLimits: Optional[List[RateLimit]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "agentId": "tasktrail-multi-agent-v1",
                "name": "TaskTrail AI Assistant",
                "description": "Multi-agent task management and planning assistant",
                "version": "1.0.0",
                "serviceEndpoint": "http://localhost:8000/a2a/v1",
                "capabilities": [
                    {
                        "id": "create_task",
                        "name": "Create Task",
                        "description": "Create and track new tasks"
                    }
                ],
                "securitySchemes": {
                    "firebase": {
                        "type": "bearer",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }


# ============================================================================
# External Agent Registration
# ============================================================================

class ExternalAgent(BaseModel):
    """Configuration for an external A2A-compatible agent"""
    agentId: str
    name: str
    description: str
    discoveryUrl: str  # URL to agent's agent-card.json
    authType: Literal["none", "apiKey", "bearer", "oauth2"]
    authCredentials: Optional[Dict[str, str]] = None  # API key, bearer token, etc.
    enabled: bool = True
    priority: int = 0  # Higher priority = preferred for matching capabilities
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# WebSocket Messages
# ============================================================================

class WSMessageType(str, Enum):
    """WebSocket message types for streaming"""
    STATE_CHANGE = "state_change"
    OUTPUT_CHUNK = "output_chunk"
    ERROR = "error"
    TASK_COMPLETE = "task_complete"
    AGENT_SWITCH = "agent_switch"
    INPUT_REQUEST = "input_request"


class WebSocketMessage(BaseModel):
    """WebSocket message envelope for streaming updates"""
    type: WSMessageType
    contextId: str
    taskId: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
