from app.firebase import get_firestore_client
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from firebase_admin import firestore
from fastapi import HTTPException
from fastapi import status as http_status
from typing import Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task-related business logic."""

    def __init__(self):
        self.db = get_firestore_client()
        self.tasks_ref = self.db.collection("tasks")

    async def create_task(self, user_id: str, task_data: TaskCreate) -> TaskResponse:
        """
        Create a new task.

        Args:
            user_id: ID of the user creating the task
            task_data: Task data from request

        Returns:
            Created task with generated ID
        """
        try:
            # Calculate position (highest position in the status + 1)
            position = await self._get_next_position(user_id, task_data.status)

            # Prepare task document
            task_dict = task_data.model_dump()
            task_dict.update({
                "userId": user_id,
                "position": position,
                "completedAt": None,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            })

            # Convert recurrence rule to dict if present
            if task_dict.get("recurrenceRule"):
                task_dict["recurrenceRule"] = task_dict["recurrenceRule"]

            # Create document
            doc_ref = self.tasks_ref.document()
            doc_ref.set(task_dict)

            # Fetch the created task
            created_task = doc_ref.get()
            task_data_dict = created_task.to_dict()
            task_data_dict["id"] = created_task.id

            logger.info(f"Task created: {created_task.id} for user {user_id}")
            return TaskResponse(**task_data_dict)

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task"
            )

    async def get_task(self, user_id: str, task_id: str) -> TaskResponse:
        """
        Get a single task by ID.

        Args:
            user_id: ID of the user
            task_id: ID of the task

        Returns:
            Task data

        Raises:
            HTTPException: If task not found or unauthorized
        """
        try:
            doc = self.tasks_ref.document(task_id).get()

            if not doc.exists:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Task not found"
                )

            task_data = doc.to_dict()

            # Verify ownership
            if task_data["userId"] != user_id:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this task"
                )

            task_data["id"] = doc.id
            return TaskResponse(**task_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get task"
            )

    async def list_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        include_completed: bool = False
    ) -> TaskListResponse:
        """
        List tasks with optional filtering.

        Args:
            user_id: ID of the user
            status: Filter by status
            project_id: Filter by project
            priority: Filter by priority
            tags: Filter by tags (any match)
            parent_task_id: Get subtasks of a parent task
            include_completed: Whether to include completed tasks

        Returns:
            List of tasks matching filters
        """
        try:
            # Start with user filter
            query = self.tasks_ref.where(filter=firestore.FieldFilter("userId", "==", user_id))

            # Apply filters (avoid inequality + orderBy to prevent index requirement)
            if status:
                query = query.where(filter=firestore.FieldFilter("status", "==", status))

            if project_id:
                query = query.where(filter=firestore.FieldFilter("projectId", "==", project_id))

            if priority:
                query = query.where(filter=firestore.FieldFilter("priority", "==", priority))

            if parent_task_id:
                query = query.where(filter=firestore.FieldFilter("parentTaskId", "==", parent_task_id))

            # Don't use order_by in Firestore query to avoid index requirements
            # We'll sort in-memory after fetching

            # Execute query
            docs = query.stream()

            tasks = []
            for doc in docs:
                task_data = doc.to_dict()
                task_data["id"] = doc.id

                # Filter completed tasks in-memory if needed
                if not include_completed and task_data.get("status") == "done":
                    continue

                # Filter by tags if specified (Firestore array-contains only supports single value)
                if tags:
                    task_tags = task_data.get("tags", [])
                    if not any(tag in task_tags for tag in tags):
                        continue

                tasks.append(TaskResponse(**task_data))

            # Sort by position in-memory (use 0 as default for tasks without position)
            tasks.sort(key=lambda t: getattr(t, 'position', 0))

            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
            return TaskListResponse(tasks=tasks, total=len(tasks))

        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list tasks"
            )

    async def get_today_tasks(self, user_id: str) -> TaskListResponse:
        """
        Get tasks for the "Today" page: overdue, due today, and high priority.

        Args:
            user_id: ID of the user

        Returns:
            Combined list of relevant tasks
        """
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            all_tasks = {}  # Use dict to deduplicate by ID

            # Get all non-completed tasks for the user and filter in-memory
            # This avoids complex composite index requirements
            query = self.tasks_ref.where(filter=firestore.FieldFilter("userId", "==", user_id))

            for doc in query.stream():
                task_data = doc.to_dict()
                task_data["id"] = doc.id

                # Skip completed tasks
                if task_data.get("status") == "done":
                    continue

                due_date = task_data.get("dueDate")
                priority = task_data.get("priority")

                # Include if: due today, overdue, or high/urgent priority
                include = False

                if due_date:
                    # Convert Firestore timestamp to datetime if needed
                    if hasattr(due_date, 'timestamp'):
                        due_date = datetime.fromtimestamp(due_date.timestamp())

                    # Due today
                    if today_start <= due_date < today_end:
                        include = True
                    # Overdue
                    elif due_date < today_start:
                        include = True

                # High/urgent priority
                if priority in ["high", "urgent"]:
                    include = True

                if include:
                    all_tasks[doc.id] = task_data

            # Convert to list and sort
            tasks = [TaskResponse(**task) for task in all_tasks.values()]

            # Sort by priority (urgent > high > medium > low), then by due date
            priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
            tasks.sort(key=lambda t: (
                priority_order.get(t.priority, 99),
                t.dueDate or datetime.max
            ))

            logger.info(f"Retrieved {len(tasks)} today tasks for user {user_id}")
            return TaskListResponse(tasks=tasks, total=len(tasks))

        except Exception as e:
            logger.error(f"Error getting today tasks: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get today tasks"
            )

    async def update_task(
        self,
        user_id: str,
        task_id: str,
        task_update: TaskUpdate
    ) -> TaskResponse:
        """
        Update an existing task.

        Args:
            user_id: ID of the user
            task_id: ID of the task to update
            task_update: Fields to update

        Returns:
            Updated task
        """
        try:
            # Get current task to verify ownership
            current_task = await self.get_task(user_id, task_id)

            # Prepare update data (only include non-None fields)
            update_data = task_update.model_dump(exclude_none=True)

            if not update_data:
                return current_task  # No changes

            # Add timestamp
            update_data["updatedAt"] = firestore.SERVER_TIMESTAMP

            # If status changed to "done", set completedAt
            if "status" in update_data and update_data["status"] == "done":
                update_data["completedAt"] = firestore.SERVER_TIMESTAMP
            elif "status" in update_data and current_task.status == "done":
                # Status changed from "done" to something else
                update_data["completedAt"] = None

            # Update document
            doc_ref = self.tasks_ref.document(task_id)
            doc_ref.update(update_data)

            # Fetch updated task
            updated_doc = doc_ref.get()
            updated_data = updated_doc.to_dict()
            updated_data["id"] = updated_doc.id

            logger.info(f"Task updated: {task_id}")
            return TaskResponse(**updated_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task"
            )

    async def delete_task(self, user_id: str, task_id: str) -> None:
        """
        Delete a task.

        Args:
            user_id: ID of the user
            task_id: ID of the task to delete
        """
        try:
            # Verify ownership
            await self.get_task(user_id, task_id)

            # Delete document
            self.tasks_ref.document(task_id).delete()

            logger.info(f"Task deleted: {task_id}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task"
            )

    async def reorder_task(
        self,
        user_id: str,
        task_id: str,
        new_position: int,
        new_status: Optional[str] = None
    ) -> TaskResponse:
        """
        Reorder a task (for drag & drop).
        Updates position and optionally status.

        Args:
            user_id: ID of the user
            task_id: ID of the task to reorder
            new_position: New position in the list
            new_status: New status if moving between columns

        Returns:
            Updated task
        """
        try:
            # Get current task
            current_task = await self.get_task(user_id, task_id)

            # Prepare update
            update_data = {
                "position": new_position,
                "updatedAt": firestore.SERVER_TIMESTAMP
            }

            if new_status and new_status != current_task.status:
                update_data["status"] = new_status
                if new_status == "done":
                    update_data["completedAt"] = firestore.SERVER_TIMESTAMP
                elif current_task.status == "done":
                    update_data["completedAt"] = None

            # Update task
            doc_ref = self.tasks_ref.document(task_id)
            doc_ref.update(update_data)

            # Fetch updated task
            updated_doc = doc_ref.get()
            updated_data = updated_doc.to_dict()
            updated_data["id"] = updated_doc.id

            logger.info(f"Task reordered: {task_id}")
            return TaskResponse(**updated_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reordering task {task_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reorder task"
            )

    async def _get_next_position(self, user_id: str, task_status: str) -> int:
        """
        Get the next position for a new task in a given status.

        Args:
            user_id: ID of the user
            task_status: Status of the task

        Returns:
            Next available position
        """
        try:
            # Get all tasks in the same status
            query = self.tasks_ref \
                .where(filter=firestore.FieldFilter("userId", "==", user_id)) \
                .where(filter=firestore.FieldFilter("status", "==", task_status)) \
                .order_by("position", direction=firestore.Query.DESCENDING) \
                .limit(1)

            docs = list(query.stream())

            if docs:
                max_position = docs[0].to_dict().get("position", 0)
                return max_position + 1
            return 0

        except Exception:
            # If query fails, default to 0
            return 0
