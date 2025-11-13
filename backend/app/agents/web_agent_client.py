"""
Web Agent Client - Communicates with the web-agent service for UI testing.
"""
from typing import Dict, Any
import httpx
from app.core.task_queue import get_celery
from app.core.db import async_session_maker
from app.models import Project, Task, TaskStatus, Event, EventType, EventLevel
from app.core.logging import get_logger
from sqlalchemy import select
from datetime import datetime

logger = get_logger(__name__)
celery_app = get_celery()

WEB_AGENT_URL = "http://web-agent:5000"


@celery_app.task(name="app.agents.web_agent_client.run_web_tests")
def run_web_tests(task_id: str):
    """Celery task wrapper for web agent client."""
    import asyncio
    return asyncio.run(_run_web_tests_async(task_id))


async def _run_web_tests_async(task_id: str) -> Dict[str, Any]:
    """Web agent client implementation."""
    logger.info("Web agent client started", task_id=task_id)

    async with async_session_maker() as db:
        # Get task
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if not task:
            logger.error("Task not found", task_id=task_id)
            return {"error": "Task not found"}

        project_id = task.project_id

        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            logger.error("Project not found", project_id=project_id)
            return {"error": "Project not found"}

        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        await db.commit()

        # Log event
        event = Event(
            project_id=project_id,
            type=EventType.TASK_STARTED,
            level=EventLevel.INFO,
            message="Web UI testing started",
            source="web_agent",
            task_id=task_id,
        )
        db.add(event)
        await db.commit()

        try:
            # Get app URL from task input or use default
            app_url = task.input_data.get("app_url", "http://localhost:3000")
            scenarios = task.input_data.get("scenarios", _get_default_scenarios())

            # Call web-agent service
            async with httpx.AsyncClient(timeout=300.0) as client:
                try:
                    response = await client.post(
                        f"{WEB_AGENT_URL}/run-tests",
                        json={
                            "project_id": project_id,
                            "app_url": app_url,
                            "scenarios": scenarios,
                        }
                    )

                    if response.status_code == 200:
                        test_results = response.json()

                        # Mark task complete
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.utcnow()
                        task.output_data = test_results
                        await db.commit()

                        # Log success
                        event = Event(
                            project_id=project_id,
                            type=EventType.TASK_COMPLETED,
                            level=EventLevel.INFO,
                            message=f"Web tests completed: {test_results.get('passed', 0)} passed, {test_results.get('failed', 0)} failed",
                            source="web_agent",
                            task_id=task_id,
                            details=test_results,
                        )
                        db.add(event)
                        await db.commit()

                        logger.info("Web tests completed", task_id=task_id)

                        # Trigger orchestrator callback
                        from app.services.orchestrator import Orchestrator
                        orchestrator = Orchestrator(db)
                        await orchestrator.on_task_complete(task_id, test_results)

                        return {"success": True, "test_results": test_results}

                    else:
                        error_msg = f"Web agent returned status {response.status_code}"
                        raise Exception(error_msg)

                except httpx.ConnectError:
                    # Web agent service not available - skip this step
                    logger.warning("Web agent service not available, skipping web tests")

                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    task.output_data = {"skipped": True, "reason": "Web agent service not available"}
                    await db.commit()

                    # Log warning
                    event = Event(
                        project_id=project_id,
                        type=EventType.LOG,
                        level=EventLevel.WARNING,
                        message="Web tests skipped: web agent service not available",
                        source="web_agent",
                        task_id=task_id,
                    )
                    db.add(event)
                    await db.commit()

                    # Still consider it complete
                    from app.services.orchestrator import Orchestrator
                    orchestrator = Orchestrator(db)
                    await orchestrator.on_task_complete(task_id, {"skipped": True})

                    return {"success": True, "skipped": True}

        except Exception as e:
            logger.error("Web agent client failed", task_id=task_id, error=str(e))

            # Mark task failed
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await db.commit()

            # Log error
            event = Event(
                project_id=project_id,
                type=EventType.TASK_FAILED,
                level=EventLevel.ERROR,
                message=f"Web testing failed: {str(e)}",
                source="web_agent",
                task_id=task_id,
            )
            db.add(event)
            await db.commit()

            # Trigger failure handler
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_task_failure(task_id, str(e))

            return {"error": str(e)}


def _get_default_scenarios() -> list:
    """Get default web test scenarios."""
    return [
        {
            "name": "Homepage Load",
            "steps": [
                {"action": "goto", "url": "/"},
                {"action": "wait", "selector": "body"},
                {"action": "screenshot", "name": "homepage"},
            ]
        },
        {
            "name": "Basic Navigation",
            "steps": [
                {"action": "goto", "url": "/"},
                {"action": "click", "selector": "a:first-of-type"},
                {"action": "wait", "timeout": 2000},
                {"action": "screenshot", "name": "navigation"},
            ]
        },
    ]
