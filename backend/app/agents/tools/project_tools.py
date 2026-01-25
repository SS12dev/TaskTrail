"""
Project Management Tools for LangChain Agents.

This module wraps ProjectService methods as LangChain tools that can be
called by AI agents to perform project operations in Firestore.
"""

from langchain_core.tools import tool
from typing import Optional
from app.services.project_service import ProjectService
from app.models.project import ProjectCreate, ProjectUpdate
import logging

logger = logging.getLogger(__name__)


class ProjectTools:
    """LangChain tools for project operations."""

    def __init__(self, user_id: str):
        """
        Initialize project tools for a specific user.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id
        self.project_service = ProjectService()

    def get_all_tools(self):
        """
        Return list of all tools with proper bindings.

        Returns:
            List of LangChain tools
        """
        async def bound_create_project(
            name: str,
            description: str = "",
            color: str = "#3B82F6",
            icon: str = "Folder"
        ) -> dict:
            """Create a new project for organizing tasks.

            Args:
                name: Project name (required)
                description: Project description
                color: Hex color code
                icon: Lucide icon name

            Returns:
                Created project with ID
            """
            try:
                project_data = ProjectCreate(
                    name=name,
                    description=description,
                    color=color,
                    icon=icon
                )

                result = await self.project_service.create_project(self.user_id, project_data)

                return {
                    "success": True,
                    "project_id": result.id,
                    "project": result.model_dump(),
                    "message": f"Created project: {result.name}"
                }
            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to create project: {str(e)}"
                }

        async def bound_list_projects(include_archived: bool = False) -> dict:
            """Get all user's projects.

            Args:
                include_archived: Include archived projects

            Returns:
                List of projects
            """
            try:
                result = await self.project_service.list_projects(self.user_id, include_archived)

                return {
                    "success": True,
                    "count": len(result.projects),
                    "projects": [p.model_dump() for p in result.projects]
                }
            except Exception as e:
                logger.error(f"Error listing projects: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to list projects: {str(e)}"
                }

        # Create tool instances with proper metadata
        create_tool = tool(bound_create_project)
        create_tool.name = "create_project"
        create_tool.description = "Create a new project for organizing tasks"

        list_tool = tool(bound_list_projects)
        list_tool.name = "list_projects"
        list_tool.description = "Get all user's projects"

        return [create_tool, list_tool]
