"""
Celery worker entry point.
"""
from app.core.task_queue import init_celery
from app.core.logging import setup_logging, get_logger
from app.core.db import init_db

# Setup
setup_logging()
init_db()

# Initialize Celery app
celery_app = init_celery()

logger = get_logger(__name__)
logger.info("Celery worker initialized")

# Export for celery command
__all__ = ["celery_app"]
