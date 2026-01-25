from app.firebase import get_firestore_client
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from firebase_admin import firestore
from fastapi import HTTPException
from fastapi import status as http_status
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project-related business logic."""

    def __init__(self):
        self.db = get_firestore_client()
        self.projects_ref = self.db.collection("projects")
        self.tasks_ref = self.db.collection("tasks")

    async def create_project(self, user_id: str, project_data: ProjectCreate) -> ProjectResponse:
        """
        Create a new project.

        Args:
            user_id: ID of the user creating the project
            project_data: Project data from request

        Returns:
            Created project with generated ID
        """
        try:
            # Prepare project document
            project_dict = project_data.model_dump()
            project_dict.update({
                "userId": user_id,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            })

            # Create document
            doc_ref = self.projects_ref.document()
            doc_ref.set(project_dict)

            # Fetch the created project
            created_project = doc_ref.get()
            project_data_dict = created_project.to_dict()
            project_data_dict["id"] = created_project.id
            project_data_dict["taskCount"] = 0

            logger.info(f"Project created: {created_project.id} for user {user_id}")
            return ProjectResponse(**project_data_dict)

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )

    async def get_project(self, user_id: str, project_id: str) -> ProjectResponse:
        """
        Get a single project by ID.

        Args:
            user_id: ID of the user
            project_id: ID of the project

        Returns:
            Project data with task count

        Raises:
            HTTPException: If project not found or unauthorized
        """
        try:
            doc = self.projects_ref.document(project_id).get()

            if not doc.exists:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            project_data = doc.to_dict()

            # Verify ownership
            if project_data["userId"] != user_id:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this project"
                )

            project_data["id"] = doc.id

            # Get task count
            task_count = await self._get_task_count(project_id, user_id)
            project_data["taskCount"] = task_count

            return ProjectResponse(**project_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get project"
            )

    async def list_projects(
        self,
        user_id: str,
        include_archived: bool = False
    ) -> ProjectListResponse:
        """
        List all projects for a user.

        Args:
            user_id: ID of the user
            include_archived: Whether to include archived projects

        Returns:
            List of projects with task counts
        """
        try:
            # Start with user filter
            query = self.projects_ref.where(filter=firestore.FieldFilter("userId", "==", user_id))

            # Filter archived if needed
            if not include_archived:
                query = query.where(filter=firestore.FieldFilter("isArchived", "==", False))

            # Order by creation date
            query = query.order_by("createdAt", direction=firestore.Query.DESCENDING)

            # Execute query
            docs = query.stream()

            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                project_data["id"] = doc.id

                # Get task count for each project
                task_count = await self._get_task_count(doc.id, user_id)
                project_data["taskCount"] = task_count

                projects.append(ProjectResponse(**project_data))

            logger.info(f"Retrieved {len(projects)} projects for user {user_id}")
            return ProjectListResponse(projects=projects, total=len(projects))

        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list projects"
            )

    async def update_project(
        self,
        user_id: str,
        project_id: str,
        project_update: ProjectUpdate
    ) -> ProjectResponse:
        """
        Update an existing project.

        Args:
            user_id: ID of the user
            project_id: ID of the project to update
            project_update: Fields to update

        Returns:
            Updated project
        """
        try:
            # Get current project to verify ownership
            current_project = await self.get_project(user_id, project_id)

            # Prepare update data (only include non-None fields)
            update_data = project_update.model_dump(exclude_none=True)

            if not update_data:
                return current_project  # No changes

            # Add timestamp
            update_data["updatedAt"] = firestore.SERVER_TIMESTAMP

            # Update document
            doc_ref = self.projects_ref.document(project_id)
            doc_ref.update(update_data)

            # Fetch updated project
            updated_doc = doc_ref.get()
            updated_data = updated_doc.to_dict()
            updated_data["id"] = updated_doc.id

            # Get task count
            task_count = await self._get_task_count(project_id, user_id)
            updated_data["taskCount"] = task_count

            logger.info(f"Project updated: {project_id}")
            return ProjectResponse(**updated_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update project"
            )

    async def delete_project(self, user_id: str, project_id: str) -> None:
        """
        Delete a project.
        Also removes projectId from all tasks in this project.

        Args:
            user_id: ID of the user
            project_id: ID of the project to delete
        """
        try:
            # Verify ownership
            await self.get_project(user_id, project_id)

            # Update all tasks in this project to remove projectId
            tasks_query = self.tasks_ref \
                .where(filter=firestore.FieldFilter("userId", "==", user_id)) \
                .where(filter=firestore.FieldFilter("projectId", "==", project_id))

            batch = self.db.batch()
            for task_doc in tasks_query.stream():
                batch.update(task_doc.reference, {"projectId": None})

            batch.commit()

            # Delete project
            self.projects_ref.document(project_id).delete()

            logger.info(f"Project deleted: {project_id}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete project"
            )

    async def _get_task_count(self, project_id: str, user_id: str) -> int:
        """
        Get the number of tasks in a project.

        Args:
            project_id: ID of the project
            user_id: ID of the user

        Returns:
            Number of tasks
        """
        try:
            # Use simple query and filter in-memory to avoid index requirement
            query = self.tasks_ref \
                .where(filter=firestore.FieldFilter("userId", "==", user_id)) \
                .where(filter=firestore.FieldFilter("projectId", "==", project_id))

            count = 0
            for doc in query.stream():
                task_data = doc.to_dict()
                if task_data.get("status") != "archived":
                    count += 1

            return count

        except Exception:
            # If query fails, return 0
            return 0
