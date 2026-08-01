"""Read-only resources — cheap context snapshots an MCP client can attach to
a conversation without an explicit tool call. All return markdown text.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .client import client
from .formatting import format_project_list, format_task_list


def register(mcp: MCPServer) -> None:
    @mcp.resource(
        "tasktrail://today",
        name="Today",
        description="Tasks due today, overdue, and high/urgent priority — the daily focus list.",
        mime_type="text/markdown",
    )
    async def today() -> str:
        result = await client.get("/tasks/today")
        return format_task_list(result["tasks"], empty_message="Nothing due today. 🎉")

    @mcp.resource(
        "tasktrail://tasks",
        name="Active tasks",
        description="All non-completed tasks across every project.",
        mime_type="text/markdown",
    )
    async def active_tasks() -> str:
        result = await client.get("/tasks/", params={"includeCompleted": False})
        return format_task_list(result["tasks"], empty_message="No active tasks.")

    @mcp.resource(
        "tasktrail://projects",
        name="Projects",
        description="All projects with their task counts.",
        mime_type="text/markdown",
    )
    async def projects() -> str:
        result = await client.get("/projects/")
        return format_project_list(result["projects"], empty_message="No projects yet.")

    @mcp.resource(
        "tasktrail://projects/{project_id}/tasks",
        name="Project tasks",
        description="All tasks belonging to a single project.",
        mime_type="text/markdown",
    )
    async def project_tasks(project_id: str) -> str:
        result = await client.get(
            "/tasks/", params={"projectId": project_id, "includeCompleted": True}
        )
        return format_task_list(
            result["tasks"], empty_message=f"No tasks in project {project_id}."
        )
