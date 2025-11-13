"""
Fixer Agent - Automatically fixes code errors and failing tests.
"""
from typing import Dict, Any
import json
from pathlib import Path
from app.core.task_queue import get_celery
from app.core.llm_router import get_llm_router, LLMRole
from app.core.db import async_session_maker
from app.models import Project, Task, TaskStatus, Event, EventType, EventLevel
from app.core.logging import get_logger
from sqlalchemy import select
from datetime import datetime

logger = get_logger(__name__)
celery_app = get_celery()


@celery_app.task(name="app.agents.fixer.run_fixer")
def run_fixer(task_id: str, error: str):
    """Celery task wrapper for fixer agent."""
    import asyncio
    return asyncio.run(_run_fixer_async(task_id, error))


async def _run_fixer_async(task_id: str, error: str) -> Dict[str, Any]:
    """Fixer agent implementation."""
    logger.info("Fixer agent started", task_id=task_id)

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

        # Log event
        event = Event(
            project_id=project_id,
            type=EventType.LOG,
            level=EventLevel.INFO,
            message=f"Auto-fix started for error: {error[:100]}",
            source="fixer",
            task_id=task_id,
        )
        db.add(event)
        await db.commit()

        try:
            workspace = Path(project.workspace_path)

            # Read relevant files for context
            error_files = _extract_files_from_error(error, workspace)
            code_context = []

            for file_path in error_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code_context.append({
                            "file": str(file_path.relative_to(workspace)),
                            "content": f.read()
                        })
                except:
                    pass

            # Call LLM for fix
            llm_router = get_llm_router()

            system_message = """You are an expert debugging and code fixing agent.
Analyze the error and code, then provide fixes.

Return your response as JSON:
{
  "analysis": "explanation of the problem",
  "fixes": [
    {
      "file": "path/to/file.py",
      "original": "code to replace",
      "fixed": "corrected code"
    }
  ]
}"""

            prompt = f"""Fix the following error in the codebase.

ERROR:
{error}

CODE FILES:
{json.dumps(code_context, indent=2)}

PROJECT SPEC:
{json.dumps(project.spec, indent=2)}

Provide fixes for the error."""

            response = await llm_router.call_llm(
                role=LLMRole.DEBUGGING,
                prompt=prompt,
                system_message=system_message,
                max_tokens=3000,
            )

            # Parse response
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            fix_data = json.loads(response_clean.strip())

            # Apply fixes
            files_fixed = []
            for fix in fix_data.get("fixes", []):
                file_path = workspace / fix["file"]
                if file_path.exists():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Apply fix
                        fixed_content = content.replace(fix["original"], fix["fixed"])

                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(fixed_content)

                        files_fixed.append(fix["file"])
                        logger.info("File fixed", file=fix["file"])

                    except Exception as e:
                        logger.warning("Failed to fix file", file=fix["file"], error=str(e))

            # Log success
            event = Event(
                project_id=project_id,
                type=EventType.ERROR_FIXED,
                level=EventLevel.INFO,
                message=f"Auto-fix completed: {len(files_fixed)} files fixed",
                source="fixer",
                task_id=task_id,
                details={
                    "analysis": fix_data.get("analysis"),
                    "files_fixed": files_fixed
                },
            )
            db.add(event)
            await db.commit()

            logger.info("Fixer agent completed", task_id=task_id, files_fixed=len(files_fixed))

            # Re-run the original task
            task.status = TaskStatus.PENDING
            task.error_message = None
            await db.commit()

            # Trigger orchestrator to reschedule
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.schedule_next_tasks(project_id)

            return {"success": True, "files_fixed": files_fixed, "analysis": fix_data.get("analysis")}

        except Exception as e:
            logger.error("Fixer agent failed", task_id=task_id, error=str(e))

            # Log error
            event = Event(
                project_id=project_id,
                type=EventType.LOG,
                level=EventLevel.ERROR,
                message=f"Auto-fix failed: {str(e)}",
                source="fixer",
                task_id=task_id,
            )
            db.add(event)
            await db.commit()

            # Mark task as permanently failed
            task.status = TaskStatus.FAILED
            task.error_message = f"Fix attempt failed: {str(e)}"
            await db.commit()

            return {"error": str(e)}


def _extract_files_from_error(error: str, workspace: Path) -> list:
    """Extract file paths mentioned in error message."""
    import re

    files = []

    # Look for file paths in error
    patterns = [
        r'File "([^"]+)"',
        r'in ([^\s]+\.py)',
        r'at ([^\s]+\.js)',
        r'([^\s]+\.ts):\d+',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, error)
        for match in matches:
            file_path = Path(match)
            if file_path.is_absolute():
                if str(workspace) in str(file_path):
                    files.append(file_path)
            else:
                full_path = workspace / file_path
                if full_path.exists():
                    files.append(full_path)

    # Deduplicate
    return list(set(files))[:5]  # Max 5 files
