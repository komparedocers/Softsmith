"""
Task queue configuration using Celery with Redis broker.
"""
from celery import Celery
from .config import get_config
from .logging import get_logger

logger = get_logger(__name__)

# Initialize Celery app
celery_app = None


def init_celery() -> Celery:
    """Initialize Celery application."""
    global celery_app

    config = get_config()
    redis_url = config.redis.url

    logger.info("Initializing Celery", broker=redis_url)

    celery_app = Celery(
        "software_maker",
        broker=redis_url,
        backend=redis_url,
        include=[
            "app.agents.planner",
            "app.agents.codegen",
            "app.agents.tester",
            "app.agents.fixer",
            "app.agents.deployer",
            "app.agents.web_agent_client",
        ]
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max
        task_soft_time_limit=3000,  # 50 minutes soft limit
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
    )

    return celery_app


def get_celery() -> Celery:
    """Get the global Celery instance."""
    global celery_app
    if celery_app is None:
        celery_app = init_celery()
    return celery_app
