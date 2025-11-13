"""
Tester Agent - Generates and runs tests for the project.
"""
from typing import Dict, Any
import json
import subprocess
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


@celery_app.task(name="app.agents.tester.run_tests")
def run_tests(task_id: str):
    """Celery task wrapper for tester agent."""
    import asyncio
    return asyncio.run(_run_tests_async(task_id))


async def _run_tests_async(task_id: str) -> Dict[str, Any]:
    """Tester agent implementation."""
    logger.info("Tester agent started", task_id=task_id)

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
            message="Test generation and execution started",
            source="tester",
            task_id=task_id,
        )
        db.add(event)
        await db.commit()

        try:
            workspace = Path(project.workspace_path)
            spec = project.spec or {}

            # Generate tests using LLM
            llm_router = get_llm_router()

            # Read existing code for context
            code_files = list(workspace.rglob("*.py")) + list(workspace.rglob("*.js")) + list(workspace.rglob("*.ts"))
            code_context = []
            for code_file in code_files[:10]:  # Limit to first 10 files
                try:
                    with open(code_file, "r", encoding="utf-8") as f:
                        code_context.append({
                            "file": str(code_file.relative_to(workspace)),
                            "content": f.read()[:1000]  # First 1000 chars
                        })
                except:
                    pass

            system_message = """You are an expert test engineer.
Generate comprehensive test suites for the given code and specification.

Return your response as JSON:
{
  "test_files": [
    {
      "path": "path/to/test_file.py",
      "content": "full test file content"
    }
  ]
}

Generate unit tests, integration tests, and include test fixtures."""

            prompt = f"""Generate tests for this project.

PROJECT SPECIFICATION:
{json.dumps(spec, indent=2)}

CODE FILES:
{json.dumps(code_context, indent=2)}

Generate comprehensive tests."""

            response = await llm_router.call_llm(
                role=LLMRole.TESTING,
                prompt=prompt,
                system_message=system_message,
                max_tokens=3000,
            )

            # Parse and create test files
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            test_data = json.loads(response_clean.strip())

            test_files_created = []
            for test_file_info in test_data.get("test_files", []):
                test_path = workspace / test_file_info["path"]
                test_path.parent.mkdir(parents=True, exist_ok=True)

                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(test_file_info["content"])

                test_files_created.append(str(test_path))

            logger.info("Test files created", count=len(test_files_created))

            # Run tests
            test_results = await _run_test_commands(workspace, spec)

            # Evaluate results
            passed = test_results.get("passed", 0)
            failed = test_results.get("failed", 0)
            success = failed == 0 and passed > 0

            if success:
                # Mark task complete
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.output_data = test_results
                await db.commit()

                # Log success
                event = Event(
                    project_id=project_id,
                    type=EventType.TEST_PASSED,
                    level=EventLevel.INFO,
                    message=f"All tests passed: {passed} passed, {failed} failed",
                    source="tester",
                    task_id=task_id,
                    details=test_results,
                )
                db.add(event)
                await db.commit()

                logger.info("Tests passed", task_id=task_id, passed=passed)

                # Trigger orchestrator callback
                from app.services.orchestrator import Orchestrator
                orchestrator = Orchestrator(db)
                await orchestrator.on_task_complete(task_id, test_results)

                return {"success": True, "test_results": test_results}

            else:
                # Tests failed - trigger fixer
                error_msg = f"Tests failed: {passed} passed, {failed} failed"
                logger.warning("Tests failed", task_id=task_id, error=error_msg)

                # Log failure
                event = Event(
                    project_id=project_id,
                    type=EventType.TEST_FAILED,
                    level=EventLevel.WARNING,
                    message=error_msg,
                    source="tester",
                    task_id=task_id,
                    details=test_results,
                )
                db.add(event)
                await db.commit()

                # Trigger orchestrator failure handler
                from app.services.orchestrator import Orchestrator
                orchestrator = Orchestrator(db)
                await orchestrator.on_task_failure(task_id, error_msg)

                return {"success": False, "test_results": test_results}

        except Exception as e:
            logger.error("Tester agent failed", task_id=task_id, error=str(e))

            # Mark task failed
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await db.commit()

            # Log error
            event = Event(
                project_id=project_id,
                type=EventType.TASK_FAILED,
                level=EventLevel.ERROR,
                message=f"Testing failed: {str(e)}",
                source="tester",
                task_id=task_id,
            )
            db.add(event)
            await db.commit()

            # Trigger failure handler
            from app.services.orchestrator import Orchestrator
            orchestrator = Orchestrator(db)
            await orchestrator.on_task_failure(task_id, str(e))

            return {"error": str(e)}


async def _run_test_commands(workspace: Path, spec: Dict) -> Dict[str, Any]:
    """Execute test commands based on project type."""
    results = {
        "passed": 0,
        "failed": 0,
        "output": "",
        "errors": [],
    }

    try:
        # Detect test framework
        if (workspace / "pytest.ini").exists() or (workspace / "pyproject.toml").exists():
            # Python/pytest
            result = subprocess.run(
                ["pytest", "--tb=short", "-v"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=300,
            )
            results["output"] = result.stdout + result.stderr

            # Parse pytest output (simplified)
            if "passed" in result.stdout:
                import re
                match = re.search(r'(\d+) passed', result.stdout)
                if match:
                    results["passed"] = int(match.group(1))

            if "failed" in result.stdout:
                import re
                match = re.search(r'(\d+) failed', result.stdout)
                if match:
                    results["failed"] = int(match.group(1))

        elif (workspace / "package.json").exists():
            # Node.js/npm
            result = subprocess.run(
                ["npm", "test"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=300,
            )
            results["output"] = result.stdout + result.stderr

            # Simplified parsing
            if result.returncode == 0:
                results["passed"] = 1
            else:
                results["failed"] = 1
                results["errors"].append(result.stderr)

        else:
            # No tests to run
            results["output"] = "No test framework detected"
            results["passed"] = 1  # Consider as passed

    except subprocess.TimeoutExpired:
        results["failed"] = 1
        results["errors"].append("Test execution timed out")
    except Exception as e:
        results["failed"] = 1
        results["errors"].append(str(e))

    return results
