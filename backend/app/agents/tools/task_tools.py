"""
Task Management Tools for LangChain Agents.

This module wraps TaskService methods as LangChain tools that can be
called by AI agents to perform actual task operations in Firestore.
"""

from langchain_core.tools import tool
from typing import Optional, List, Literal
from app.services.task_service import TaskService
from app.models.task import TaskCreate, TaskUpdate
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def _parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string in various formats to datetime object.
    
    Handles:
    - ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    - Natural language: "tomorrow", "next week", "next friday"
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object or None if unparseable
    """
    if not date_str:
        return None
        
    date_str = date_str.lower().strip()
    today = datetime.now().date()
    
    # Try ISO format first
    try:
        return datetime.fromisoformat(date_str)
    except:
        pass
    
    # Handle natural language dates
    if "tomorrow" in date_str:
        return datetime.combine(today + timedelta(days=1), datetime.min.time())
    elif "today" in date_str:
        return datetime.combine(today, datetime.min.time())
    elif "next week" in date_str:
        return datetime.combine(today + timedelta(days=7), datetime.min.time())
    elif "next" in date_str and any(day in date_str for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        weekday_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
        for day_name, day_num in weekday_map.items():
            if day_name in date_str:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return datetime.combine(today + timedelta(days=days_ahead), datetime.min.time())
    elif "in 3" in date_str or "3 days" in date_str:
        return datetime.combine(today + timedelta(days=3), datetime.min.time())
    elif "in 7" in date_str or "week" in date_str:
        return datetime.combine(today + timedelta(days=7), datetime.min.time())
    
    # Default fallback - return current datetime
    logger.warning(f"Could not parse date: {date_str}, using current datetime")
    return datetime.now()


class TaskTools:
    """LangChain tools for task operations."""

    def __init__(self, user_id: str):
        """
        Initialize task tools for a specific user.

        Args:
            user_id: The user's Firebase UID
        """
        self.user_id = user_id
        self.task_service = TaskService()

    @tool
    async def create_task(
        title: str,
        description: str = "",
        priority: Literal["low", "medium", "high", "urgent"] = "medium",
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None
    ) -> dict:
        """Create a new task in the user's task list.

        Args:
            title: Task title (required)
            description: Detailed description
            priority: Task priority (low/medium/high/urgent)
            due_date: Due date in ISO format (YYYY-MM-DD)
            tags: List of tags for categorization
            project_id: ID of project to assign task to

        Returns:
            Created task with ID and all fields
        """
        # This will be dynamically bound to the instance
        return {}

    @tool
    async def update_task(
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[Literal["todo", "in_progress", "done", "archived"]] = None,
        priority: Optional[Literal["low", "medium", "high", "urgent"]] = None,
        due_date: Optional[str] = None
    ) -> dict:
        """Update an existing task.

        Args:
            task_id: ID of task to update (required)
            title: New title
            description: New description
            status: New status (todo/in_progress/done/archived)
            priority: New priority
            due_date: New due date in ISO format

        Returns:
            Updated task information
        """
        return {}

    @tool
    async def list_tasks(
        status: Optional[Literal["todo", "in_progress", "done", "archived"]] = None,
        priority: Optional[Literal["low", "medium", "high", "urgent"]] = None,
        project_id: Optional[str] = None,
        include_completed: bool = False
    ) -> dict:
        """Query and filter tasks.

        Args:
            status: Filter by status
            priority: Filter by priority
            project_id: Filter by project
            include_completed: Include completed tasks

        Returns:
            List of matching tasks
        """
        return {}

    @tool
    async def get_today_tasks() -> dict:
        """Get tasks for today's smart inbox (overdue + due today + high priority).

        Returns:
            Tasks that need attention today
        """
        return {}

    @tool
    async def delete_task(task_id: str) -> dict:
        """Delete a task permanently.

        Args:
            task_id: ID of task to delete

        Returns:
            Confirmation message
        """
        return {}

    def get_all_tools(self):
        """
        Return list of all tools with proper bindings.

        Returns:
            List of LangChain tools
        """
        # Create instance-bound versions of the tools
        async def bound_create_task(
            title: str,
            description: str = "",
            priority: Literal["low", "medium", "high", "urgent"] = "medium",
            due_date: Optional[str] = None,
            tags: Optional[List[str]] = None,
            project_id: Optional[str] = None
        ) -> dict:
            """Create a new task in the user's task list."""
            try:
                # Parse the due date using flexible parsing
                parsed_due_date = _parse_date_string(due_date) if due_date else None
                
                task_data = TaskCreate(
                    title=title,
                    description=description,
                    priority=priority,
                    dueDate=parsed_due_date,
                    tags=tags or [],
                    projectId=project_id
                )

                result = await self.task_service.create_task(self.user_id, task_data)

                return {
                    "success": True,
                    "task_id": result.id,
                    "task": result.model_dump(),
                    "message": f"Created task: {result.title}"
                }
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to create task: {str(e)}"
                }

        async def bound_update_task(
            task_id: str,
            title: Optional[str] = None,
            description: Optional[str] = None,
            status: Optional[Literal["todo", "in_progress", "done", "archived"]] = None,
            priority: Optional[Literal["low", "medium", "high", "urgent"]] = None,
            due_date: Optional[str] = None
        ) -> dict:
            """Update an existing task."""
            try:
                updates = {}
                if title: updates["title"] = title
                if description: updates["description"] = description
                if status: updates["status"] = status
                if priority: updates["priority"] = priority
                if due_date: 
                    parsed_date = _parse_date_string(due_date)
                    if parsed_date:
                        updates["dueDate"] = parsed_date

                update_data = TaskUpdate(**updates)
                result = await self.task_service.update_task(self.user_id, task_id, update_data)

                return {
                    "success": True,
                    "task": result.model_dump(),
                    "message": f"Updated task: {result.title}"
                }
            except Exception as e:
                logger.error(f"Error updating task: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to update task: {str(e)}"
                }

        async def bound_list_tasks(
            status: Optional[Literal["todo", "in_progress", "done", "archived"]] = None,
            priority: Optional[Literal["low", "medium", "high", "urgent"]] = None,
            project_id: Optional[str] = None,
            include_completed: bool = False
        ) -> dict:
            """Query and filter tasks."""
            try:
                result = await self.task_service.list_tasks(
                    self.user_id,
                    status=status,
                    priority=priority,
                    project_id=project_id,
                    include_completed=include_completed
                )

                return {
                    "success": True,
                    "count": len(result.tasks),
                    "tasks": [t.model_dump() for t in result.tasks]
                }
            except Exception as e:
                logger.error(f"Error listing tasks: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to list tasks: {str(e)}"
                }

        async def bound_get_today_tasks() -> dict:
            """Get tasks for today's smart inbox (overdue + due today + high priority)."""
            try:
                result = await self.task_service.get_today_tasks(self.user_id)

                return {
                    "success": True,
                    "count": len(result.tasks),
                    "tasks": [t.model_dump() for t in result.tasks],
                    "message": f"You have {len(result.tasks)} tasks that need attention"
                }
            except Exception as e:
                logger.error(f"Error getting today tasks: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to get today's tasks: {str(e)}"
                }

        async def bound_delete_task(task_id: str) -> dict:
            """Delete a task permanently."""
            try:
                await self.task_service.delete_task(self.user_id, task_id)

                return {
                    "success": True,
                    "message": f"Task {task_id} deleted successfully"
                }
            except Exception as e:
                logger.error(f"Error deleting task: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to delete task: {str(e)}"
                }

        # Create tool instances with proper metadata
        create_tool = tool(bound_create_task)
        create_tool.name = "create_task"
        create_tool.description = "Create a new task in the user's task list"

        update_tool = tool(bound_update_task)
        update_tool.name = "update_task"
        update_tool.description = "Update an existing task"

        list_tool = tool(bound_list_tasks)
        list_tool.name = "list_tasks"
        list_tool.description = "Query and filter tasks"

        today_tool = tool(bound_get_today_tasks)
        today_tool.name = "get_today_tasks"
        today_tool.description = "Get tasks for today's smart inbox"

        delete_tool = tool(bound_delete_task)
        delete_tool.name = "delete_task"
        delete_tool.description = "Delete a task permanently"

        return [create_tool, update_tool, list_tool, today_tool, delete_tool]
