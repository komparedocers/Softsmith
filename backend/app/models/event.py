"""
Event model - represents timeline events and logs.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.db import Base
import uuid


class EventLevel(str, Enum):
    """Log/event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(str, Enum):
    """Types of events."""
    PROJECT_CREATED = "project_created"
    PROJECT_STARTED = "project_started"
    PROJECT_COMPLETED = "project_completed"
    PROJECT_FAILED = "project_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    CODE_GENERATED = "code_generated"
    TEST_RUN = "test_run"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    ERROR_FIXED = "error_fixed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    LOG = "log"


class Event(Base):
    """Timeline event/log entry."""
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    type = Column(SQLEnum(EventType), nullable=False)
    level = Column(SQLEnum(EventLevel), default=EventLevel.INFO, nullable=False)

    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional structured data

    # Source information
    source = Column(String, nullable=True)  # Which agent/component generated this
    task_id = Column(String, nullable=True)  # Related task if applicable

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="events")

    def to_dict(self):
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type.value,
            "level": self.level.value,
            "message": self.message,
            "details": self.details,
            "source": self.source,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
