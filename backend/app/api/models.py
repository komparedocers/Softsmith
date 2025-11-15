"""
Pydantic models for API requests and responses.
"""
from typing import Optional
from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""
    prompt: str
    name: Optional[str] = None
    user_id: str = "system"


class ApiResponse(BaseModel):
    """Generic API response."""
    message: str
    success: bool = True


class ProjectStats(BaseModel):
    """Project statistics."""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    progress_percentage: float


class EventResponse(BaseModel):
    """Event response model."""
    id: str
    project_id: str
    type: str
    level: str
    message: str
    timestamp: str
    source: Optional[str] = None
    task_id: Optional[str] = None
    details: Optional[dict] = None
