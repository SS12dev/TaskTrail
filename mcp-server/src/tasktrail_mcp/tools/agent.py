"""Delegates natural-language requests to the backend's LangGraph multi-agent
system (`POST /api/v1/agent/chat`). This incurs LLM cost + latency on the
backend, on top of the calling MCP client's own model — prefer the direct
CRUD tools (tasktrail_create_task, tasktrail_list_tasks, etc.) for anything
that's really just "create/update/list X". Reach for this tool when the
request needs multi-step planning or fuzzy interpretation the backend agents
are specifically built for (e.g. "break this project into tasks").
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from ..client import client
from ..config import settings


def register(mcp: MCPServer) -> None:
    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=True))
    async def tasktrail_ask_agent(message: str) -> dict[str, Any]:
        """Send a natural-language message to TaskTrail's own AI assistant
        (a supervisor + planner/executor/query/conversation agent system).

        Good for: "plan my week", "break project X down into tasks",
        "what should I focus on today and why". Not needed for simple CRUD —
        use tasktrail_create_task / tasktrail_list_tasks / etc. directly for
        those, they're faster and cheaper.

        This call can take noticeably longer than other tools since it runs
        the backend's own LLM chain (up to a couple of minutes).
        """
        return await client.post(
            "/agent/chat",
            json={"message": message},
            timeout=settings.agent_timeout_seconds,
        )
