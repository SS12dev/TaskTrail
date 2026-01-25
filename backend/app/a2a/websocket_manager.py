"""
WebSocket Connection Manager

Manages WebSocket connections for A2A streaming updates.
"""

from fastapi import WebSocket
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import logging
import asyncio

from app.models.a2a_models import TaskState, WSMessageType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for streaming A2A updates

    Features:
    - Multiple connections per context
    - User-based connection tracking
    - Broadcast to all connections in a context
    - Connection limits per user
    """

    def __init__(self):
        # context_id -> list of WebSocket connections
        self._connections: Dict[str, List[WebSocket]] = {}

        # websocket -> (context_id, user_id)
        self._connection_metadata: Dict[WebSocket, tuple[str, str, datetime]] = {}

        # user_id -> set of WebSocket connections
        self._user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        context_id: str,
        user_id: str,
    ):
        """
        Register a new WebSocket connection

        Args:
            websocket: WebSocket connection
            context_id: Context identifier
            user_id: User identifier
        """
        # Track by context
        if context_id not in self._connections:
            self._connections[context_id] = []
        self._connections[context_id].append(websocket)

        # Track metadata
        self._connection_metadata[websocket] = (context_id, user_id, datetime.utcnow())

        # Track by user
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(websocket)

        logger.info(
            f"WebSocket connected - contextId: {context_id}, user: {user_id}, "
            f"total connections: {len(self._connections[context_id])}"
        )

    async def disconnect(self, websocket: WebSocket, context_id: str):
        """
        Unregister a WebSocket connection

        Args:
            websocket: WebSocket connection
            context_id: Context identifier
        """
        # Remove from context connections
        if context_id in self._connections:
            if websocket in self._connections[context_id]:
                self._connections[context_id].remove(websocket)

            # Clean up empty context
            if not self._connections[context_id]:
                del self._connections[context_id]

        # Remove metadata and user tracking
        if websocket in self._connection_metadata:
            _, user_id, _ = self._connection_metadata[websocket]
            del self._connection_metadata[websocket]

            # Remove from user connections
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(websocket)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]

        logger.info(f"WebSocket disconnected - contextId: {context_id}")

    async def send_update(
        self,
        context_id: str,
        message: Dict[str, Any],
    ):
        """
        Send update to all connections in a context

        Args:
            context_id: Context identifier
            message: Message to send
        """
        if context_id not in self._connections:
            logger.warning(f"No connections found for context: {context_id}")
            return

        connections = self._connections[context_id].copy()
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected WebSockets
        for websocket in disconnected:
            await self.disconnect(websocket, context_id)

    async def broadcast_state_change(
        self,
        context_id: str,
        task_id: str,
        task_state: TaskState,
        message: Optional[str] = None,
        progress: Optional[float] = None,
    ):
        """
        Broadcast task state change to all connections

        Args:
            context_id: Context identifier
            task_id: Task identifier
            task_state: New task state
            message: Optional status message
            progress: Optional progress (0.0-1.0)
        """
        data = {
            "taskState": task_state.value,
            "taskId": task_id,
        }

        if message:
            data["message"] = message
        if progress is not None:
            data["progress"] = progress

        await self.send_update(
            context_id,
            {
                "type": WSMessageType.STATE_CHANGE.value,
                "contextId": context_id,
                "taskId": task_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.info(
            f"Broadcast state change - contextId: {context_id}, "
            f"taskId: {task_id}, state: {task_state.value}"
        )

    async def stream_agent_output(
        self,
        context_id: str,
        task_id: str,
        chunk: str,
        agent_name: Optional[str] = None,
    ):
        """
        Stream partial output chunk from agent

        Args:
            context_id: Context identifier
            task_id: Task identifier
            chunk: Output chunk
            agent_name: Optional agent name
        """
        data = {
            "chunk": chunk,
            "taskId": task_id,
        }

        if agent_name:
            data["agent"] = agent_name

        await self.send_update(
            context_id,
            {
                "type": WSMessageType.OUTPUT_CHUNK.value,
                "contextId": context_id,
                "taskId": task_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def notify_agent_switch(
        self,
        context_id: str,
        task_id: str,
        from_agent: Optional[str],
        to_agent: str,
        reason: Optional[str] = None,
    ):
        """
        Notify about agent handoff

        Args:
            context_id: Context identifier
            task_id: Task identifier
            from_agent: Previous agent name
            to_agent: New agent name
            reason: Optional reason for switch
        """
        data = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "taskId": task_id,
        }

        if reason:
            data["reason"] = reason

        await self.send_update(
            context_id,
            {
                "type": WSMessageType.AGENT_SWITCH.value,
                "contextId": context_id,
                "taskId": task_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.info(
            f"Agent switch - contextId: {context_id}, "
            f"from: {from_agent} -> to: {to_agent}"
        )

    async def send_error(
        self,
        context_id: str,
        task_id: str,
        error_message: str,
        error_code: Optional[str] = None,
    ):
        """
        Send error notification

        Args:
            context_id: Context identifier
            task_id: Task identifier
            error_message: Error message
            error_code: Optional error code
        """
        data = {
            "error": error_message,
            "taskId": task_id,
        }

        if error_code:
            data["error_code"] = error_code

        await self.send_update(
            context_id,
            {
                "type": WSMessageType.ERROR.value,
                "contextId": context_id,
                "taskId": task_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.error(
            f"WebSocket error sent - contextId: {context_id}, "
            f"error: {error_message}"
        )

    async def request_input(
        self,
        context_id: str,
        task_id: str,
        prompt: str,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Request input from user

        Args:
            context_id: Context identifier
            task_id: Task identifier
            prompt: Input prompt
            input_schema: Optional JSON schema for expected input
        """
        data = {
            "prompt": prompt,
            "taskId": task_id,
        }

        if input_schema:
            data["input_schema"] = input_schema

        await self.send_update(
            context_id,
            {
                "type": WSMessageType.INPUT_REQUEST.value,
                "contextId": context_id,
                "taskId": task_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.info(f"Input requested - contextId: {context_id}, prompt: {prompt}")

    def get_connection_count(self, context_id: str) -> int:
        """
        Get number of active connections for a context

        Args:
            context_id: Context identifier

        Returns:
            Number of active connections
        """
        return len(self._connections.get(context_id, []))

    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of active connections for a user

        Args:
            user_id: User identifier

        Returns:
            Number of active connections
        """
        return len(self._user_connections.get(user_id, set()))

    async def keep_alive(self, websocket: WebSocket, interval: int = 20):
        """
        Send periodic ping to keep connection alive

        Args:
            websocket: WebSocket connection
            interval: Ping interval in seconds
        """
        try:
            while True:
                await asyncio.sleep(interval)
                await websocket.send_json({"type": "ping"})
        except Exception as e:
            logger.debug(f"Keep-alive stopped: {e}")


# Global connection manager instance
manager = ConnectionManager()
