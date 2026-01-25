from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.services.project_service import ProjectService
from typing import Dict, Any

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new project.

    Projects help organize tasks into categories.
    Each project has a name, color, and icon for visual identification.
    """
    service = ProjectService()
    return await service.create_project(user["uid"], project)


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    includeArchived: bool = Query(False, description="Include archived projects"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all projects.

    By default, archived projects are hidden.
    Each project includes a taskCount showing the number of active tasks.
    """
    service = ProjectService()
    return await service.list_projects(user["uid"], includeArchived)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific project by ID.

    Returns 404 if project doesn't exist or user doesn't have access.
    """
    service = ProjectService()
    return await service.get_project(user["uid"], project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a project.

    Only provided fields will be updated. All fields are optional.
    Use isArchived=true to archive a project without deleting it.
    """
    service = ProjectService()
    return await service.update_project(user["uid"], project_id, project_update)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a project.

    All tasks in this project will have their projectId removed.
    Returns 204 No Content on success.
    """
    service = ProjectService()
    await service.delete_project(user["uid"], project_id)
    return None
