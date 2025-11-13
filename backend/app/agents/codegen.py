"""
Code Generation Agent - Generates source code based on specifications.
"""
from typing import Dict, Any, List
import json
from pathlib import Path
from app.core.task_queue import get_celery
from app.core.llm_router import get_llm_router, LLMRole
from app.core.db import async_session_maker
from app.models import Project, Task, TaskStatus, Event, EventType, EventLevel
from app.core.logging import get_logger
from sqlalchemy import select
from datetime import datetime
import os

logger = get_logger(__name__)
celery_app = get_celery()


@celery_app.task(name="app.agents.codegen.run_codegen")
def run_codegen(task_id: str):
    """Celery task wrapper for code generation agent."""
    import asyncio
    return asyncio.run(_run_codegen_async(task_id))


async def _run_codegen_async(task_id: str) -> Dict[str, Any]:
    """Code generation agent implementation."""
    logger.info("Codegen agent started", task_id=task_id)

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
            message=f"Code generation started for {task.name}",
            source="codegen",
            task_id=task_id,
        )
        db.add(event)
        await db.commit()

        try:
            component = task.input_data.get("component", "backend")
            spec = task.input_data.get("spec", {})
            project_spec = project.spec or {}

            # Prepare workspace
            workspace = Path(project.workspace_path)
            workspace.mkdir(parents=True, exist_ok=True)

            # Call LLM for code generation
            llm_router = get_llm_router()

            system_message = f"""You are an expert software developer.
Generate production-ready, well-structured code based on the specification.

Return your response as JSON with this structure:
{{
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "full file content here"
    }},
    ...
  ]
}}

Generate clean, documented, and functional code."""

            prompt = f"""Generate code for the {component} component.

PROJECT SPECIFICATION:
{json.dumps(project_spec, indent=2)}

COMPONENT SPECIFICATION:
{json.dumps(spec, indent=2)}

ORIGINAL PROMPT:
{project.prompt}

Generate all necessary files for this component."""

            response = await llm_router.call_llm(
                role=LLMRole.CODE_GENERATION,
                prompt=prompt,
                system_message=system_message,
                max_tokens=4000,
            )

            # Parse response
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            result = json.loads(response_clean.strip())

            # Write files
            files_created = []
            for file_info in result.get("files", []):
                file_path = workspace / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_info["content"])

                files_created.append(str(file_path))
                logger.info("File created", path=file_info["path"])

            # Mark task complete
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.output_data = {"files_created": files_created}
            await db.commit()

            # Log success event
            event = Event(
                project_id=project_id,
                type=EventType.CODE_GENERATED,
                level=EventLevel.INFO,
                message=f"Code generated: {len(files_created)} files created",
                source="codegen",
                task_id=task_id,
                details={"files": files_created[:10]},  # Limit to first 10
            )
            db.add(event)
            await db.commit()

            logger.info("Codegen agent completed", task_id=task_id, files_count=len(files_created))

            # Trigger orchestrator callback
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_task_complete(task_id, {"files_created": files_created})

            return {"success": True, "files_created": files_created}

        except Exception as e:
            logger.error("Codegen agent failed", task_id=task_id, error=str(e))

            # Mark task failed
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await db.commit()

            # Log error
            event = Event(
                project_id=project_id,
                type=EventType.TASK_FAILED,
                level=EventLevel.ERROR,
                message=f"Code generation failed: {str(e)}",
                source="codegen",
                task_id=task_id,
            )
            db.add(event)
            await db.commit()

            # Trigger failure handler
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_task_failure(task_id, str(e))

            return {"error": str(e)}
