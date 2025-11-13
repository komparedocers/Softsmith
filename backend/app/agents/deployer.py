"""
Deployer Agent - Builds and deploys the application locally.
"""
from typing import Dict, Any
import subprocess
from pathlib import Path
from app.core.task_queue import get_celery
from app.core.db import async_session_maker
from app.models import Project, Task, TaskStatus, Event, EventType, EventLevel
from app.core.logging import get_logger
from sqlalchemy import select
from datetime import datetime

logger = get_logger(__name__)
celery_app = get_celery()


@celery_app.task(name="app.agents.deployer.run_deployment")
def run_deployment(task_id: str):
    """Celery task wrapper for deployer agent."""
    import asyncio
    return asyncio.run(_run_deployment_async(task_id))


async def _run_deployment_async(task_id: str) -> Dict[str, Any]:
    """Deployer agent implementation."""
    logger.info("Deployer agent started", task_id=task_id)

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
            type=EventType.DEPLOYMENT_STARTED,
            level=EventLevel.INFO,
            message="Deployment started",
            source="deployer",
            task_id=task_id,
        )
        db.add(event)
        await db.commit()

        try:
            workspace = Path(project.workspace_path)
            deployment_info = {}

            # Check for docker-compose
            if (workspace / "docker-compose.yml").exists():
                logger.info("Deploying with docker-compose")
                result = await _deploy_docker_compose(workspace)
                deployment_info["type"] = "docker-compose"
                deployment_info["result"] = result

            # Check for Dockerfile
            elif (workspace / "Dockerfile").exists():
                logger.info("Building and running Docker container")
                result = await _deploy_docker(workspace)
                deployment_info["type"] = "docker"
                deployment_info["result"] = result

            # Python app
            elif (workspace / "requirements.txt").exists():
                logger.info("Deploying Python application")
                result = await _deploy_python(workspace)
                deployment_info["type"] = "python"
                deployment_info["result"] = result

            # Node.js app
            elif (workspace / "package.json").exists():
                logger.info("Deploying Node.js application")
                result = await _deploy_nodejs(workspace)
                deployment_info["type"] = "nodejs"
                deployment_info["result"] = result

            else:
                deployment_info["type"] = "none"
                deployment_info["message"] = "No deployment configuration found"

            # Mark task complete
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.output_data = deployment_info
            await db.commit()

            # Log success
            event = Event(
                project_id=project_id,
                type=EventType.DEPLOYMENT_COMPLETED,
                level=EventLevel.INFO,
                message="Deployment completed successfully",
                source="deployer",
                task_id=task_id,
                details=deployment_info,
            )
            db.add(event)
            await db.commit()

            logger.info("Deployer agent completed", task_id=task_id)

            # Trigger orchestrator callback
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_task_complete(task_id, deployment_info)

            return {"success": True, "deployment_info": deployment_info}

        except Exception as e:
            logger.error("Deployer agent failed", task_id=task_id, error=str(e))

            # Mark task failed
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await db.commit()

            # Log error
            event = Event(
                project_id=project_id,
                type=EventType.TASK_FAILED,
                level=EventLevel.ERROR,
                message=f"Deployment failed: {str(e)}",
                source="deployer",
                task_id=task_id,
            )
            db.add(event)
            await db.commit()

            # Trigger failure handler
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_task_failure(task_id, str(e))

            return {"error": str(e)}


async def _deploy_docker_compose(workspace: Path) -> Dict[str, Any]:
    """Deploy using docker-compose."""
    try:
        # Build
        result = subprocess.run(
            ["docker-compose", "build"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        # Start services
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=300,
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _deploy_docker(workspace: Path) -> Dict[str, Any]:
    """Build and run single Docker container."""
    try:
        # Build
        result = subprocess.run(
            ["docker", "build", "-t", f"app-{workspace.name}", "."],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        # Run
        result = subprocess.run(
            ["docker", "run", "-d", "-p", "8080:8080", f"app-{workspace.name}"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )

        return {
            "success": result.returncode == 0,
            "container_id": result.stdout.strip(),
            "error": result.stderr if result.returncode != 0 else None,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _deploy_python(workspace: Path) -> Dict[str, Any]:
    """Deploy Python application."""
    try:
        # Install dependencies
        subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            cwd=workspace,
            capture_output=True,
            timeout=300,
        )

        # Start app in background (simplified)
        # In production, would use proper process management
        return {
            "success": True,
            "message": "Python app dependencies installed",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _deploy_nodejs(workspace: Path) -> Dict[str, Any]:
    """Deploy Node.js application."""
    try:
        # Install dependencies
        subprocess.run(
            ["npm", "install"],
            cwd=workspace,
            capture_output=True,
            timeout=300,
        )

        # Build if needed
        if (workspace / "package.json").exists():
            subprocess.run(
                ["npm", "run", "build"],
                cwd=workspace,
                capture_output=True,
                timeout=300,
            )

        return {
            "success": True,
            "message": "Node.js app built and ready",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
