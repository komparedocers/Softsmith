"""
Task model - represents individual tasks within a project.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.db import Base
import uuid


class TaskType(str, Enum):
    """Types of tasks in the project workflow."""
    PLANNING = "planning"
    CODEGEN = "codegen"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DEPLOYMENT = "deployment"
    WEB_TEST = "web_test"
    REVIEW = "review"
    DOCUMENTATION = "documentation"


class TaskStatus(str, Enum):
    """Task execution states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class Task(Base):
    """Individual task within a project."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # Task details
    input_data = Column(JSON, nullable=True)  # Input parameters for the task
    output_data = Column(JSON, nullable=True)  # Results/output
    error_message = Column(Text, nullable=True)

    # Dependencies
    depends_on = Column(JSON, nullable=True)  # List of task IDs this task depends on

    # Execution tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(String, default="0")

    # Celery task ID
    celery_task_id = Column(String, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")

    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "depends_on": self.depends_on,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "celery_task_id": self.celery_task_id,
        }
