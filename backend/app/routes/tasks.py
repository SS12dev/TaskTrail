from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.services.task_service import TaskService
from typing import Dict, Any, Optional, List

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new task.

    All tasks are automatically associated with the authenticated user.
    """
    service = TaskService()
    return await service.create_task(user["uid"], task)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    projectId: Optional[str] = Query(None, description="Filter by project ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    parentTaskId: Optional[str] = Query(None, description="Get subtasks of a parent task"),
    includeCompleted: bool = Query(False, description="Include completed tasks"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all tasks with optional filtering.

    Filters:
    - status: Filter by task status (todo, in_progress, done, archived)
    - projectId: Show only tasks from a specific project
    - priority: Filter by priority level (low, medium, high, urgent)
    - tags: Filter by tags (matches any tag)
    - parentTaskId: Get subtasks of a parent task
    - includeCompleted: Whether to include completed tasks (default: false)
    """
    service = TaskService()
    return await service.list_tasks(
        user["uid"],
        status=status,
        project_id=projectId,
        priority=priority,
        tags=tags,
        parent_task_id=parentTaskId,
        include_completed=includeCompleted
    )


@router.get("/today", response_model=TaskListResponse)
async def get_today_tasks(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get tasks for the "Today" page.

    Returns a smart inbox with:
    - Tasks due today
    - Overdue tasks
    - High priority and urgent tasks

    Tasks are sorted by priority and due date.
    """
    service = TaskService()
    return await service.get_today_tasks(user["uid"])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific task by ID.

    Returns 404 if task doesn't exist or user doesn't have access.
    """
    service = TaskService()
    return await service.get_task(user["uid"], task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a task.

    Only provided fields will be updated. All fields are optional.
    Automatically sets completedAt when status changes to "done".
    """
    service = TaskService()
    return await service.update_task(user["uid"], task_id, task_update)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a task.

    Returns 204 No Content on success.
    """
    service = TaskService()
    await service.delete_task(user["uid"], task_id)
    return None


@router.post("/{task_id}/reorder", response_model=TaskResponse)
async def reorder_task(
    task_id: str,
    newPosition: int = Query(..., description="New position in the list"),
    newStatus: Optional[str] = Query(None, description="New status if moving between columns"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reorder a task (for drag & drop in kanban board).

    Updates the task's position and optionally its status.
    Used when dragging tasks within a column or between columns.
    """
    service = TaskService()
    return await service.reorder_task(user["uid"], task_id, newPosition, newStatus)
