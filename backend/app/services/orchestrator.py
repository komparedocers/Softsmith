"""
Orchestrator service - the brain that coordinates all agents and project workflows.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Project, ProjectStatus,
    Task, TaskType, TaskStatus,
    Event, EventType, EventLevel
)
from app.core.logging import get_logger, LoggerMixin
from app.core.config import get_config
from pathlib import Path
import json

logger = get_logger(__name__)


class Orchestrator(LoggerMixin):
    """
    Orchestrates the entire software generation workflow.
    Manages project lifecycle and coordinates agents.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.config = get_config()

    async def create_project(self, prompt: str, user_id: str = "system") -> Project:
        """Create a new project and schedule planning."""
        from app.services.project_service import ProjectService

        project_service = ProjectService(self.db)
        project = await project_service.create_project(prompt, user_id)

        # Set workspace path
        projects_dir = Path(self.config.app.projects_dir)
        projects_dir.mkdir(parents=True, exist_ok=True)

        project.workspace_path = str(projects_dir / project.id)
        Path(project.workspace_path).mkdir(parents=True, exist_ok=True)

        await self.db.commit()

        # Schedule planning task
        await self.schedule_planning(project.id)

        self.logger.info("Project created and planning scheduled", project_id=project.id)
        return project

    async def schedule_planning(self, project_id: str):
        """Schedule the planning agent task."""
        task = Task(
            project_id=project_id,
            name="Project Planning",
            description="Analyze prompt and create project specification",
            type=TaskType.PLANNING,
            status=TaskStatus.PENDING,
        )

        self.db.add(task)
        await self.db.commit()

        # Enqueue Celery task
        from app.agents.planner import run_planner
        celery_task = run_planner.delay(project_id, task.id)
        task.celery_task_id = celery_task.id
        task.status = TaskStatus.QUEUED

        await self.db.commit()

        self.logger.info("Planning task scheduled", project_id=project_id, task_id=task.id)

    async def on_planning_complete(self, project_id: str, spec: Dict[str, Any]):
        """Handle completion of planning phase."""
        project = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project.scalar_one_or_none()

        if not project:
            self.logger.error("Project not found", project_id=project_id)
            return

        # Save spec
        project.spec = spec
        project.status = ProjectStatus.CODING
        project.started_at = datetime.utcnow()
        await self.db.commit()

        # Create tasks from spec
        await self.create_tasks_from_spec(project_id, spec)

        self.logger.info("Planning complete, tasks created", project_id=project_id)

        # Schedule next tasks
        await self.schedule_next_tasks(project_id)

    async def create_tasks_from_spec(self, project_id: str, spec: Dict[str, Any]):
        """Create task DAG from project specification."""
        tasks = []

        # Backend tasks
        if spec.get("backend"):
            tasks.append(Task(
                project_id=project_id,
                name="Generate Backend Code",
                description="Generate backend application code",
                type=TaskType.CODEGEN,
                status=TaskStatus.PENDING,
                input_data={"component": "backend", "spec": spec.get("backend")},
            ))

        # Frontend tasks
        if spec.get("frontend"):
            tasks.append(Task(
                project_id=project_id,
                name="Generate Frontend Code",
                description="Generate frontend application code",
                type=TaskType.CODEGEN,
                status=TaskStatus.PENDING,
                input_data={"component": "frontend", "spec": spec.get("frontend")},
            ))

        # Infrastructure tasks
        if spec.get("infrastructure"):
            tasks.append(Task(
                project_id=project_id,
                name="Generate Infrastructure",
                description="Generate Docker, k8s, and deployment configs",
                type=TaskType.CODEGEN,
                status=TaskStatus.PENDING,
                input_data={"component": "infrastructure", "spec": spec.get("infrastructure")},
            ))

        # Testing tasks (depend on code generation)
        tasks.append(Task(
            project_id=project_id,
            name="Generate and Run Tests",
            description="Generate test suite and execute tests",
            type=TaskType.TESTING,
            status=TaskStatus.PENDING,
            depends_on=[],  # Will be filled after code tasks
        ))

        # Deployment task (depends on tests passing)
        tasks.append(Task(
            project_id=project_id,
            name="Deploy Application",
            description="Build and deploy the application locally",
            type=TaskType.DEPLOYMENT,
            status=TaskStatus.PENDING,
            depends_on=[],  # Will be filled after test task
        ))

        # Add tasks to DB
        for task in tasks:
            self.db.add(task)

        await self.db.flush()

        # Set up dependencies
        code_task_ids = [t.id for t in tasks if t.type == TaskType.CODEGEN]
        test_tasks = [t for t in tasks if t.type == TaskType.TESTING]
        deploy_tasks = [t for t in tasks if t.type == TaskType.DEPLOYMENT]

        for test_task in test_tasks:
            test_task.depends_on = code_task_ids

        for deploy_task in deploy_tasks:
            deploy_task.depends_on = [t.id for t in test_tasks]

        # Update project task counts
        project = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project.scalar_one()
        project.total_tasks = len(tasks)

        await self.db.commit()

    async def schedule_next_tasks(self, project_id: str):
        """Schedule all tasks that are ready to run."""
        # Get all pending tasks
        result = await self.db.execute(
            select(Task).where(
                Task.project_id == project_id,
                Task.status == TaskStatus.PENDING
            )
        )
        pending_tasks = list(result.scalars().all())

        for task in pending_tasks:
            if await self._task_is_ready(task):
                await self._schedule_task(task)

    async def _task_is_ready(self, task: Task) -> bool:
        """Check if all dependencies for a task are completed."""
        if not task.depends_on:
            return True

        # Check if all dependency tasks are completed
        for dep_id in task.depends_on:
            dep_result = await self.db.execute(
                select(Task).where(Task.id == dep_id)
            )
            dep_task = dep_result.scalar_one_or_none()

            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _schedule_task(self, task: Task):
        """Schedule a specific task to appropriate agent."""
        self.logger.info("Scheduling task", task_id=task.id, task_type=task.type.value)

        task.status = TaskStatus.QUEUED
        await self.db.commit()

        # Route to appropriate agent
        if task.type == TaskType.CODEGEN:
            from app.agents.codegen import run_codegen
            celery_task = run_codegen.delay(task.id)
            task.celery_task_id = celery_task.id

        elif task.type == TaskType.TESTING:
            from app.agents.tester import run_tests
            celery_task = run_tests.delay(task.id)
            task.celery_task_id = celery_task.id

        elif task.type == TaskType.DEPLOYMENT:
            from app.agents.deployer import run_deployment
            celery_task = run_deployment.delay(task.id)
            task.celery_task_id = celery_task.id

        elif task.type == TaskType.WEB_TEST:
            from app.agents.web_agent_client import run_web_tests
            celery_task = run_web_tests.delay(task.id)
            task.celery_task_id = celery_task.id

        await self.db.commit()

    async def on_task_complete(self, task_id: str, output: Dict[str, Any]):
        """Handle task completion."""
        task = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task.scalar_one_or_none()

        if not task:
            self.logger.error("Task not found", task_id=task_id)
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.output_data = output

        # Update project stats
        project = await self.db.execute(
            select(Project).where(Project.id == task.project_id)
        )
        project = project.scalar_one()
        project.completed_tasks += 1

        await self.db.commit()

        self.logger.info("Task completed", task_id=task_id, project_id=task.project_id)

        # Schedule next tasks
        await self.schedule_next_tasks(task.project_id)

        # Check if project is complete
        await self._check_project_completion(task.project_id)

    async def on_task_failure(self, task_id: str, error: str):
        """Handle task failure and trigger fix agent if applicable."""
        task = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task.scalar_one_or_none()

        if not task:
            self.logger.error("Task not found", task_id=task_id)
            return

        retry_count = int(task.retry_count)
        max_retries = self.config.app.max_retries

        if retry_count < max_retries:
            self.logger.info("Task failed, attempting fix", task_id=task_id, retry=retry_count)

            task.status = TaskStatus.RETRYING
            task.retry_count = str(retry_count + 1)
            task.error_message = error
            await self.db.commit()

            # Trigger fix agent
            from app.agents.fixer import run_fixer
            celery_task = run_fixer.delay(task.id, error)
            task.celery_task_id = celery_task.id
            await self.db.commit()

        else:
            self.logger.error("Task failed permanently", task_id=task_id)

            task.status = TaskStatus.FAILED
            task.error_message = error
            await self.db.commit()

            # Update project
            project = await self.db.execute(
                select(Project).where(Project.id == task.project_id)
            )
            project = project.scalar_one()
            project.failed_tasks += 1
            project.status = ProjectStatus.FAILED
            project.last_error = f"Task {task.name} failed: {error}"
            await self.db.commit()

    async def _check_project_completion(self, project_id: str):
        """Check if all project tasks are complete."""
        project = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project.scalar_one_or_none()

        if not project:
            return

        # Get all tasks
        tasks_result = await self.db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        tasks = list(tasks_result.scalars().all())

        # Check if all are completed
        all_complete = all(t.status == TaskStatus.COMPLETED for t in tasks)

        if all_complete:
            project.status = ProjectStatus.READY
            project.completed_at = datetime.utcnow()
            await self.db.commit()

            self.logger.info("Project completed successfully!", project_id=project_id)
