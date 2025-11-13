"""
Planner Agent - Analyzes prompts and creates detailed project specifications.
"""
from typing import Dict, Any
import json
from app.core.task_queue import get_celery
from app.core.llm_router import get_llm_router, LLMRole
from app.core.db import async_session_maker
from app.models import Project, Task, TaskStatus, Event, EventType, EventLevel
from app.core.logging import get_logger
from sqlalchemy import select
from datetime import datetime

logger = get_logger(__name__)
celery_app = get_celery()


@celery_app.task(name="app.agents.planner.run_planner")
def run_planner(project_id: str, task_id: str):
    """
    Celery task wrapper for planner agent.
    """
    import asyncio
    return asyncio.run(_run_planner_async(project_id, task_id))


async def _run_planner_async(project_id: str, task_id: str) -> Dict[str, Any]:
    """
    Planner agent implementation.
    Analyzes the project prompt and creates a detailed specification.
    """
    logger.info("Planner agent started", project_id=project_id, task_id=task_id)

    async with async_session_maker() as db:
        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            logger.error("Project not found", project_id=project_id)
            return {"error": "Project not found"}

        # Get task
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if task:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await db.commit()

        # Log event
        event = Event(
            project_id=project_id,
            type=EventType.TASK_STARTED,
            level=EventLevel.INFO,
            message="Planning agent started analyzing project",
            source="planner",
            task_id=task_id,
        )
        db.add(event)
        await db.commit()

        try:
            # Call LLM for planning
            llm_router = get_llm_router()

            system_message = """You are an expert software architect and project planner.
Your job is to analyze a user's software request and create a detailed technical specification.

Return your response as valid JSON with this structure:
{
  "project_name": "suggested name",
  "description": "detailed description",
  "tech_stack": {
    "backend": ["language/framework", ...],
    "frontend": ["framework", ...],
    "database": ["type"],
    "infrastructure": ["docker", "kubernetes", ...]
  },
  "backend": {
    "framework": "name",
    "language": "name",
    "modules": ["module1", "module2", ...],
    "api_type": "REST/GraphQL/gRPC"
  },
  "frontend": {
    "framework": "name",
    "components": ["comp1", "comp2", ...]
  },
  "database": {
    "type": "postgres/mongodb/etc",
    "tables": ["table1", "table2", ...]
  },
  "infrastructure": {
    "deployment": "docker-compose/k8s",
    "services": ["api", "web", "db", ...]
  },
  "features": ["feature1", "feature2", ...],
  "test_strategy": {
    "unit_tests": true,
    "integration_tests": true,
    "e2e_tests": true
  }
}"""

            prompt = f"""Analyze this software request and create a detailed technical specification:

USER REQUEST:
{project.prompt}

Create a comprehensive spec that can be used to generate working code."""

            response = await llm_router.call_llm(
                role=LLMRole.PLANNING,
                prompt=prompt,
                system_message=system_message,
                max_tokens=2000,
            )

            # Parse JSON response
            # Clean the response - remove markdown code blocks if present
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            spec = json.loads(response_clean.strip())

            # Save spec to project
            project.spec = spec
            if "project_name" in spec:
                project.name = spec["project_name"]
            if "description" in spec:
                project.description = spec["description"]

            await db.commit()

            # Mark task complete
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.output_data = spec
                await db.commit()

            # Log success
            event = Event(
                project_id=project_id,
                type=EventType.TASK_COMPLETED,
                level=EventLevel.INFO,
                message="Planning completed successfully",
                source="planner",
                task_id=task_id,
                details={"spec_keys": list(spec.keys())},
            )
            db.add(event)
            await db.commit()

            logger.info("Planner agent completed", project_id=project_id)

            # Trigger orchestrator callback
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_planning_complete(project_id, spec)

            return {"success": True, "spec": spec}

        except Exception as e:
            logger.error("Planner agent failed", project_id=project_id, error=str(e))

            # Mark task failed
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await db.commit()

            # Log error
            event = Event(
                project_id=project_id,
                type=EventType.TASK_FAILED,
                level=EventLevel.ERROR,
                message=f"Planning failed: {str(e)}",
                source="planner",
                task_id=task_id,
            )
            db.add(event)
            await db.commit()

            return {"error": str(e)}
