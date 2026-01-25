from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    """
    Base project model with common fields.
    Used as a foundation for create and update operations.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(default="", max_length=1000, description="Project description")
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$", description="Project color (hex)")
    icon: str = Field(default="Folder", description="Lucide icon name")
    isArchived: bool = Field(default=False, description="Whether the project is archived")


class ProjectCreate(ProjectBase):
    """
    Model for creating a new project.
    Inherits all fields from ProjectBase.
    """
    pass


class ProjectUpdate(BaseModel):
    """
    Model for updating an existing project.
    All fields are optional to support partial updates.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    isArchived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """
    Model for project responses from the API.
    Includes all base fields plus system-generated fields.
    """
    id: str = Field(..., description="Unique project identifier")
    userId: str = Field(..., description="ID of the user who owns this project")
    taskCount: Optional[int] = Field(default=0, description="Number of tasks in this project")
    createdAt: datetime = Field(..., description="When the project was created")
    updatedAt: datetime = Field(..., description="When the project was last updated")


class ProjectListResponse(BaseModel):
    """
    Model for list of projects.
    """
    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
