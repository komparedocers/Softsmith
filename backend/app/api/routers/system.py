"""
System verification and health check endpoints.
"""
from fastapi import APIRouter
from app.core.config import get_config, get_settings
from app.core.llm_router import get_llm_router
from app.core.logging import get_logger
from app.core.db import engine
from sqlalchemy import text
import redis
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/system", tags=["system"])


@router.get("/verify")
async def verify_system():
    """
    Comprehensive system verification.
    Checks all components and returns detailed status.
    """
    results = {
        "overall_status": "healthy",
        "components": {},
        "warnings": [],
        "errors": []
    }

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        results["components"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        results["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        results["errors"].append(f"Database: {str(e)}")
        results["overall_status"] = "unhealthy"

    # Check Redis
    try:
        config = get_config()
        r = redis.from_url(config.redis.url)
        r.ping()
        results["components"]["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        results["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
        results["errors"].append(f"Redis: {str(e)}")
        results["overall_status"] = "unhealthy"

    # Check LLM configuration
    try:
        config = get_config()
        settings = get_settings()

        llm_status = {
            "mode": config.llm.mode,
            "providers": {}
        }

        # Check each provider
        for provider_name, provider_config in config.llm.providers.items():
            if provider_config.enabled:
                # Check if API key is set (for cloud providers)
                if provider_name == "openai":
                    has_key = bool(settings.openai_api_key)
                    llm_status["providers"][provider_name] = {
                        "enabled": True,
                        "configured": has_key,
                        "model": provider_config.model
                    }
                    if not has_key:
                        results["warnings"].append(f"OpenAI API key not set")

                elif provider_name == "claude":
                    has_key = bool(settings.anthropic_api_key)
                    llm_status["providers"][provider_name] = {
                        "enabled": True,
                        "configured": has_key,
                        "model": provider_config.model
                    }
                    if not has_key:
                        results["warnings"].append(f"Claude API key not set")

                elif provider_name == "local":
                    llm_status["providers"][provider_name] = {
                        "enabled": True,
                        "configured": True,
                        "base_url": provider_config.base_url,
                        "model": provider_config.model
                    }

        # Check if at least one provider is configured
        any_configured = any(
            p.get("configured", False)
            for p in llm_status["providers"].values()
        )

        if not any_configured:
            results["warnings"].append(
                "No LLM provider is properly configured. "
                "Please set API keys or configure local LLM."
            )
            if results["overall_status"] == "healthy":
                results["overall_status"] = "degraded"

        results["components"]["llm"] = llm_status

    except Exception as e:
        results["components"]["llm"] = {"status": "error", "error": str(e)}
        results["errors"].append(f"LLM: {str(e)}")

    # Check file system
    try:
        config = get_config()
        projects_dir = config.app.projects_dir

        if os.path.exists(projects_dir):
            results["components"]["filesystem"] = {
                "status": "healthy",
                "projects_dir": projects_dir,
                "writable": os.access(projects_dir, os.W_OK)
            }

            if not os.access(projects_dir, os.W_OK):
                results["warnings"].append(f"Projects directory not writable: {projects_dir}")

        else:
            results["components"]["filesystem"] = {
                "status": "warning",
                "message": f"Projects directory does not exist: {projects_dir}"
            }
            results["warnings"].append(f"Projects directory missing: {projects_dir}")

    except Exception as e:
        results["components"]["filesystem"] = {"status": "error", "error": str(e)}
        results["errors"].append(f"Filesystem: {str(e)}")

    # Check Celery workers (attempt)
    try:
        from app.core.task_queue import get_celery
        celery_app = get_celery()

        # Try to inspect workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            worker_count = len(active_workers)
            results["components"]["workers"] = {
                "status": "healthy",
                "count": worker_count,
                "workers": list(active_workers.keys())
            }
        else:
            results["components"]["workers"] = {
                "status": "warning",
                "message": "No active workers detected"
            }
            results["warnings"].append("No Celery workers are running")

    except Exception as e:
        results["components"]["workers"] = {
            "status": "unknown",
            "message": "Could not connect to workers"
        }
        results["warnings"].append("Could not verify worker status")

    return results


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes-style readiness probe.
    Returns 200 if system is ready to accept requests.
    """
    try:
        # Check critical components only
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        config = get_config()
        r = redis.from_url(config.redis.url)
        r.ping()

        return {"status": "ready"}

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not ready", "error": str(e)}, 503


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if application is alive.
    """
    return {"status": "alive"}
