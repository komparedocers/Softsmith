"""
Project service - business logic for managing projects.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Project, ProjectStatus, Task, TaskType, TaskStatus, Event, EventType, EventLevel
from app.core.logging import get_logger
from pathlib import Path
import uuid

logger = get_logger(__name__)


class ProjectService:
    """Service for managing software projects."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_project(
        self,
        prompt: str,
        user_id: str = "system",
        name: Optional[str] = None,
        config_overrides: Optional[Dict] = None
    ) -> Project:
        """Create a new project from a prompt."""
        project = Project(
            id=str(uuid.uuid4()),
            name=name or f"Project-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            description=prompt[:200],  # Truncate for description
            prompt=prompt,
            user_id=user_id,
            status=ProjectStatus.NEW,
            config_overrides=config_overrides or {},
        )

        self.db.add(project)
        await self.db.flush()

        # Create initial event
        event = Event(
            project_id=project.id,
            type=EventType.PROJECT_CREATED,
            level=EventLevel.INFO,
            message=f"Project '{project.name}' created",
            source="project_service",
        )
        self.db.add(event)
        await self.db.commit()

        logger.info("Project created", project_id=project.id, name=project.name)
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        user_id: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Project]:
        """List projects with optional filtering."""
        query = select(Project)

        if user_id:
            query = query.where(Project.user_id == user_id)

        if status:
            query = query.where(Project.status == status)

        query = query.order_by(Project.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        error_message: Optional[str] = None
    ) -> Optional[Project]:
        """Update project status."""
        project = await self.get_project(project_id)
        if not project:
            return None

        old_status = project.status
        project.status = status
        project.updated_at = datetime.utcnow()

        if status == ProjectStatus.FAILED and error_message:
            project.last_error = error_message
            project.error_count += 1

        if status in [ProjectStatus.READY, ProjectStatus.DEPLOYED]:
            project.completed_at = datetime.utcnow()

        # Create status change event
        event = Event(
            project_id=project_id,
            type=EventType.PROJECT_COMPLETED if status == ProjectStatus.READY else EventType.LOG,
            level=EventLevel.ERROR if status == ProjectStatus.FAILED else EventLevel.INFO,
            message=f"Project status changed from {old_status.value} to {status.value}",
            details={"old_status": old_status.value, "new_status": status.value},
            source="project_service",
        )
        self.db.add(event)

        await self.db.commit()
        logger.info("Project status updated", project_id=project_id, status=status.value)
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its related data."""
        project = await self.get_project(project_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.commit()

        logger.info("Project deleted", project_id=project_id)
        return True

    async def get_project_stats(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project statistics."""
        project = await self.get_project(project_id)
        if not project:
            return None

        # Count tasks by status
        result = await self.db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        tasks = list(result.scalars().all())

        stats = {
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running_tasks": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
            "completed_tasks": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "progress_percentage": (
                (len([t for t in tasks if t.status == TaskStatus.COMPLETED]) / len(tasks) * 100)
                if tasks else 0
            ),
        }

        return stats

    async def pause_project(self, project_id: str) -> Optional[Project]:
        """Pause a project."""
        return await self.update_project_status(project_id, ProjectStatus.PAUSED)

    async def resume_project(self, project_id: str) -> Optional[Project]:
        """Resume a paused project."""
        project = await self.get_project(project_id)
        if not project or project.status != ProjectStatus.PAUSED:
            return None

        # Resume with the last active status
        # For now, just set to CODING
        return await self.update_project_status(project_id, ProjectStatus.CODING)
