"""
A2A (Agent-to-Agent) Protocol Integration Package

This package provides A2A protocol support for TaskTrail, enabling:
- A2A Server: Expose TaskTrail agents via A2A protocol
- A2A Client: Call external A2A-compatible agents
- WebSocket streaming for real-time task updates
- Agent discovery via Agent Card

Modules:
- adapters: Convert between A2A and TaskTrail formats
- agent_card: Generate and serve TaskTrail's Agent Card
- client: Discover and communicate with external agents
- websocket_manager: Manage WebSocket connections for streaming
"""

from app.models.a2a_models import (
    A2AMessage,
    A2AResponse,
    AgentCard,
    AgentCapability,
    ExternalAgent,
    TaskState,
    TaskUpdate,
    WebSocketMessage,
    WSMessageType,
)

__all__ = [
    "A2AMessage",
    "A2AResponse",
    "AgentCard",
    "AgentCapability",
    "ExternalAgent",
    "TaskState",
    "TaskUpdate",
    "WebSocketMessage",
    "WSMessageType",
]
