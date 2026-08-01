"""Task CRUD tools — thin wrappers over `POST/GET/PATCH/DELETE /api/v1/tasks`.

Domain enums (must match backend `app/models/task.py` exactly):
  status:   todo | in_progress | done | archived
  priority: low | medium | high | urgent
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from ..client import client
from ..formatting import format_task_list

Status = Literal["todo", "in_progress", "done", "archived"]
Priority = Literal["low", "medium", "high", "urgent"]
ResponseFormat = Literal["markdown", "json"]


def _render(tasks: list[dict[str, Any]], response_format: ResponseFormat, *, empty: str) -> Any:
    if response_format == "json":
        return tasks
    return format_task_list(tasks, empty_message=empty)


def register(mcp: MCPServer) -> None:
    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
    async def tasktrail_create_task(
        title: str,
        description: str = "",
        status: Status = "todo",
        priority: Priority = "medium",
        dueDate: str | None = None,
        tags: list[str] | None = None,
        projectId: str | None = None,
        parentTaskId: str | None = None,
    ) -> dict[str, Any]:
        """Create a new task.

        Args:
            title: Task title (required, 1-200 chars).
            description: Longer free-text description.
            status: One of todo, in_progress, done, archived. Defaults to todo.
            priority: One of low, medium, high, urgent. Defaults to medium.
            dueDate: ISO 8601 date or datetime (e.g. "2026-08-15"), if any.
            tags: List of freeform tag strings.
            projectId: ID of the project this task belongs to, if any. Use
                tasktrail_list_projects to find valid IDs.
            parentTaskId: ID of the parent task, if this is a subtask.

        Returns the created task, including its generated `id`.
        """
        body = {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "dueDate": dueDate,
            "tags": tags or [],
            "projectId": projectId,
            "parentTaskId": parentTaskId,
        }
        return await client.post("/tasks/", json=body)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def tasktrail_list_tasks(
        status: Status | None = None,
        projectId: str | None = None,
        priority: Priority | None = None,
        tags: list[str] | None = None,
        parentTaskId: str | None = None,
        includeCompleted: bool = False,
        response_format: ResponseFormat = "markdown",
    ) -> Any:
        """List tasks with optional filters.

        By default, completed tasks are excluded — set includeCompleted=True
        to see them too. Use response_format="json" to get full task objects
        (every field) instead of the compact markdown summary.
        """
        result = await client.get(
            "/tasks/",
            params={
                "status": status,
                "projectId": projectId,
                "priority": priority,
                "tags": tags,
                "parentTaskId": parentTaskId,
                "includeCompleted": includeCompleted,
            },
        )
        return _render(result["tasks"], response_format, empty="No tasks match those filters.")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def tasktrail_get_today_tasks(response_format: ResponseFormat = "markdown") -> Any:
        """Get the "Today" smart inbox: tasks due today, overdue tasks, and
        high/urgent priority tasks, sorted by priority and due date."""
        result = await client.get("/tasks/today")
        return _render(result["tasks"], response_format, empty="Nothing due today. 🎉")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def tasktrail_get_task(task_id: str) -> dict[str, Any]:
        """Get full details for a single task by its ID."""
        return await client.get(f"/tasks/{task_id}")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
    async def tasktrail_update_task(
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        status: Status | None = None,
        priority: Priority | None = None,
        dueDate: str | None = None,
        tags: list[str] | None = None,
        projectId: str | None = None,
    ) -> dict[str, Any]:
        """Partially update a task. Only the fields you pass are changed.

        To mark a task complete, call with status="done" — completedAt is set
        automatically by the backend. To move a task to a different project,
        pass projectId (or "" to clear it, if the backend treats empty as
        None — prefer omitting the field over guessing).
        """
        body = {
            k: v
            for k, v in {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "dueDate": dueDate,
                "tags": tags,
                "projectId": projectId,
            }.items()
            if v is not None
        }
        return await client.patch(f"/tasks/{task_id}", json=body)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True))
    async def tasktrail_delete_task(task_id: str) -> str:
        """Permanently delete a task. This cannot be undone — confirm the
        task ID with tasktrail_get_task or tasktrail_list_tasks first if
        there's any ambiguity about which task the user means."""
        await client.delete(f"/tasks/{task_id}")
        return f"Task {task_id} deleted."
