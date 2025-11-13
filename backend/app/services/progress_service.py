"""
Progress service - tracks and reports project progress.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Project, Task, Event, EventType, EventLevel, Artifact
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProgressService:
    """Service for tracking and reporting progress."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log_event(
        self,
        project_id: str,
        event_type: EventType,
        message: str,
        level: EventLevel = EventLevel.INFO,
        source: Optional[str] = None,
        task_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Event:
        """Log an event for a project."""
        event = Event(
            project_id=project_id,
            type=event_type,
            level=level,
            message=message,
            source=source,
            task_id=task_id,
            details=details or {},
        )

        self.db.add(event)
        await self.db.commit()

        logger.info(
            "Event logged",
            project_id=project_id,
            event_type=event_type.value,
            message=message
        )
        return event

    async def get_project_events(
        self,
        project_id: str,
        limit: int = 100,
        offset: int = 0,
        level: Optional[EventLevel] = None,
        event_type: Optional[EventType] = None
    ) -> List[Event]:
        """Get events for a project."""
        query = select(Event).where(Event.project_id == project_id)

        if level:
            query = query.where(Event.level == level)

        if event_type:
            query = query.where(Event.type == event_type)

        query = query.order_by(Event.timestamp.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task_events(
        self,
        task_id: str,
        limit: int = 50
    ) -> List[Event]:
        """Get events related to a specific task."""
        query = select(Event).where(Event.task_id == task_id)
        query = query.order_by(Event.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_project_timeline(self, project_id: str) -> Dict[str, Any]:
        """Get a timeline view of project progress."""
        project = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project.scalar_one_or_none()

        if not project:
            return {}

        # Get all tasks
        tasks_result = await self.db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
        )
        tasks = list(tasks_result.scalars().all())

        # Get all events
        events_result = await self.db.execute(
            select(Event).where(Event.project_id == project_id).order_by(Event.timestamp)
        )
        events = list(events_result.scalars().all())

        timeline = {
            "project": project.to_dict(),
            "phases": [],
            "tasks": [t.to_dict() for t in tasks],
            "events": [e.to_dict() for e in events],
            "milestones": self._extract_milestones(tasks, events),
        }

        return timeline

    def _extract_milestones(self, tasks: List[Task], events: List[Event]) -> List[Dict]:
        """Extract key milestones from tasks and events."""
        milestones = []

        # Planning completed
        planning_tasks = [t for t in tasks if t.type.value == "planning"]
        if planning_tasks and any(t.status.value == "completed" for t in planning_tasks):
            milestone = max(planning_tasks, key=lambda t: t.completed_at or datetime.min)
            milestones.append({
                "name": "Planning Completed",
                "timestamp": milestone.completed_at.isoformat() if milestone.completed_at else None,
                "type": "planning"
            })

        # First code generated
        codegen_events = [e for e in events if e.type == EventType.CODE_GENERATED]
        if codegen_events:
            first_code = min(codegen_events, key=lambda e: e.timestamp)
            milestones.append({
                "name": "First Code Generated",
                "timestamp": first_code.timestamp.isoformat(),
                "type": "codegen"
            })

        # Tests passing
        test_passed_events = [e for e in events if e.type == EventType.TEST_PASSED]
        if test_passed_events:
            first_pass = min(test_passed_events, key=lambda e: e.timestamp)
            milestones.append({
                "name": "Tests Passing",
                "timestamp": first_pass.timestamp.isoformat(),
                "type": "testing"
            })

        # Deployment
        deploy_events = [e for e in events if e.type == EventType.DEPLOYMENT_COMPLETED]
        if deploy_events:
            deploy = min(deploy_events, key=lambda e: e.timestamp)
            milestones.append({
                "name": "Deployment Completed",
                "timestamp": deploy.timestamp.isoformat(),
                "type": "deployment"
            })

        return milestones

    async def get_artifacts(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Artifact]:
        """Get artifacts for a project."""
        query = select(Artifact).where(Artifact.project_id == project_id)
        query = query.order_by(Artifact.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_artifact(
        self,
        project_id: str,
        name: str,
        artifact_type: str,
        file_path: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        **kwargs
    ) -> Artifact:
        """Add an artifact to the project."""
        artifact = Artifact(
            project_id=project_id,
            name=name,
            type=artifact_type,
            file_path=file_path,
            description=description,
            created_by=created_by,
            **kwargs
        )

        self.db.add(artifact)
        await self.db.commit()

        logger.info(
            "Artifact added",
            project_id=project_id,
            artifact_name=name,
            artifact_type=artifact_type
        )
        return artifact
