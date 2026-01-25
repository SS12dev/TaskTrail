from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class RecurrenceRule(BaseModel):
    """
    Recurrence rule for recurring tasks.
    Supports daily, weekly, monthly, and yearly patterns.
    """
    pattern: Literal["daily", "weekly", "monthly", "yearly"]
    interval: int = Field(default=1, ge=1, description="Repeat every N days/weeks/months/years")
    daysOfWeek: Optional[List[int]] = Field(default=None, description="Days of week for weekly pattern (0=Sunday, 6=Saturday)")
    endDate: Optional[datetime] = Field(default=None, description="When to stop generating recurring tasks")
    lastGenerated: Optional[datetime] = Field(default=None, description="Last time a recurring instance was generated")


class TaskBase(BaseModel):
    """
    Base task model with common fields.
    Used as a foundation for create and update operations.
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(default="", max_length=2000, description="Task description")
    status: Literal["todo", "in_progress", "done", "archived"] = Field(default="todo", description="Task status")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="medium", description="Task priority")
    dueDate: Optional[datetime] = Field(default=None, description="When the task is due")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    projectId: Optional[str] = Field(default=None, description="ID of the project this task belongs to")
    parentTaskId: Optional[str] = Field(default=None, description="ID of the parent task (for subtasks)")
    isRecurring: bool = Field(default=False, description="Whether this task recurs")
    recurrenceRule: Optional[RecurrenceRule] = Field(default=None, description="Recurrence pattern if task is recurring")


class TaskCreate(TaskBase):
    """
    Model for creating a new task.
    Inherits all fields from TaskBase.
    """
    pass


class TaskUpdate(BaseModel):
    """
    Model for updating an existing task.
    All fields are optional to support partial updates.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[Literal["todo", "in_progress", "done", "archived"]] = None
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None
    dueDate: Optional[datetime] = None
    tags: Optional[List[str]] = None
    projectId: Optional[str] = None
    position: Optional[int] = Field(None, ge=0, description="Position for ordering (used in drag & drop)")
    isRecurring: Optional[bool] = None
    recurrenceRule: Optional[RecurrenceRule] = None


class TaskResponse(TaskBase):
    """
    Model for task responses from the API.
    Includes all base fields plus system-generated fields.
    """
    id: str = Field(..., description="Unique task identifier")
    userId: str = Field(..., description="ID of the user who owns this task")
    position: int = Field(..., description="Position for ordering within status/project")
    completedAt: Optional[datetime] = Field(default=None, description="When the task was completed")
    createdAt: datetime = Field(..., description="When the task was created")
    updatedAt: datetime = Field(..., description="When the task was last updated")


class TaskListResponse(BaseModel):
    """
    Model for paginated list of tasks.
    """
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks matching the query")
