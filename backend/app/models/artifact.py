"""
Artifact model - represents generated files, reports, and outputs.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.db import Base
import uuid


class ArtifactType(str, Enum):
    """Types of artifacts."""
    SOURCE_CODE = "source_code"
    TEST_REPORT = "test_report"
    BUILD_OUTPUT = "build_output"
    DEPLOYMENT_LOG = "deployment_log"
    SCREENSHOT = "screenshot"
    DOCUMENTATION = "documentation"
    ARCHIVE = "archive"
    CONFIG = "config"
    OTHER = "other"


class Artifact(Base):
    """Generated artifact/file."""
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    type = Column(SQLEnum(ArtifactType), nullable=False)
    description = Column(Text, nullable=True)

    # File information
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)

    # Download URL
    url = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=True)  # Which agent/task created this

    # Relationships
    project = relationship("Project", back_populates="artifacts")

    def to_dict(self):
        """Convert artifact to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }
