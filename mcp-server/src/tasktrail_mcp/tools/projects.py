"""Project CRUD tools — thin wrappers over `POST/GET/PATCH/DELETE /api/v1/projects`."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from ..client import client
from ..formatting import format_project_list

ResponseFormat = Literal["markdown", "json"]


def register(mcp: MCPServer) -> None:
    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
    async def tasktrail_create_project(
        name: str,
        description: str = "",
        color: str = "#3B82F6",
        icon: str = "Folder",
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            name: Project name (required, 1-100 chars).
            description: Longer free-text description.
            color: Hex color, e.g. "#3B82F6" (used by the frontend UI).
            icon: A Lucide icon name (e.g. "Folder", "Briefcase", "Rocket").

        Returns the created project, including its generated `id`.
        """
        body = {"name": name, "description": description, "color": color, "icon": icon}
        return await client.post("/projects/", json=body)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def tasktrail_list_projects(response_format: ResponseFormat = "markdown") -> Any:
        """List all projects, with task counts. Archived projects are
        included — check the `isArchived` field / "(archived)" marker."""
        result = await client.get("/projects/")
        if response_format == "json":
            return result["projects"]
        return format_project_list(result["projects"], empty_message="No projects yet.")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def tasktrail_get_project(project_id: str) -> dict[str, Any]:
        """Get full details for a single project by its ID."""
        return await client.get(f"/projects/{project_id}")

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
    async def tasktrail_update_project(
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        isArchived: bool | None = None,
    ) -> dict[str, Any]:
        """Partially update a project. Only the fields you pass are changed.

        To archive a project, call with isArchived=True. Archiving does not
        delete or touch its tasks.
        """
        body = {
            k: v
            for k, v in {
                "name": name,
                "description": description,
                "color": color,
                "icon": icon,
                "isArchived": isArchived,
            }.items()
            if v is not None
        }
        return await client.patch(f"/projects/{project_id}", json=body)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True))
    async def tasktrail_delete_project(project_id: str) -> str:
        """Permanently delete a project. This cannot be undone. Its tasks are
        NOT deleted — they become unassigned (projectId cleared). Confirm the
        project ID with tasktrail_list_projects first if there's any
        ambiguity about which project the user means."""
        await client.delete(f"/projects/{project_id}")
        return f"Project {project_id} deleted."
