"""
Agents API router - endpoints for managing agent workers.
"""
from fastapi import APIRouter
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status")
async def get_agents_status():
    """Get status of all agent workers."""
    # In production, query Celery worker stats
    return {
        "workers": [
            {
                "name": "worker-1",
                "status": "active",
                "tasks_completed": 42,
                "tasks_running": 2,
            }
        ],
        "total_workers": 1,
        "active_workers": 1,
    }


@router.get("/capabilities")
async def get_agent_capabilities():
    """Get capabilities of available agents."""
    return {
        "agents": [
            {
                "name": "planner",
                "description": "Project planning and specification generation",
                "capabilities": ["planning", "architecture"]
            },
            {
                "name": "codegen",
                "description": "Code generation from specifications",
                "capabilities": ["code_generation", "backend", "frontend"]
            },
            {
                "name": "tester",
                "description": "Test generation and execution",
                "capabilities": ["testing", "unit_tests", "integration_tests"]
            },
            {
                "name": "fixer",
                "description": "Automatic error fixing",
                "capabilities": ["debugging", "error_fixing"]
            },
            {
                "name": "deployer",
                "description": "Application deployment",
                "capabilities": ["deployment", "docker", "kubernetes"]
            },
            {
                "name": "web_agent",
                "description": "Web UI testing with Playwright",
                "capabilities": ["web_testing", "ui_testing", "e2e_testing"]
            },
        ]
    }
