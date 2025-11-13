"""
Projects API router - endpoints for managing projects.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.db import get_db
from app.models import Project, ProjectStatus
from app.services.project_service import ProjectService
from app.services.progress_service import ProgressService
from app.services.orchestrator import Orchestrator
from app.core.logging import get_logger
import json

logger = get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    prompt: str
    name: Optional[str] = None
    user_id: str = "system"


class ProjectUpdate(BaseModel):
    status: Optional[ProjectStatus] = None
    name: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    prompt: str
    status: str
    user_id: str
    created_at: str
    updated_at: str
    workspace_path: Optional[str]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int

    class Config:
        from_attributes = True


@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project from a prompt."""
    logger.info("Creating new project", prompt_length=len(project_data.prompt))

    orchestrator = Orchestrator(db)
    project = await orchestrator.create_project(
        prompt=project_data.prompt,
        user_id=project_data.user_id
    )

    return ProjectResponse(**project.to_dict())


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    user_id: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all projects with optional filtering."""
    project_service = ProjectService(db)
    projects = await project_service.list_projects(
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return [ProjectResponse(**p.to_dict()) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID."""
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**project.to_dict())


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a project."""
    project_service = ProjectService(db)

    if update_data.status:
        project = await project_service.update_project_status(project_id, update_data.status)
    else:
        project = await project_service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**project.to_dict())


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project."""
    project_service = ProjectService(db)
    success = await project_service.delete_project(project_id)

    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get project statistics."""
    project_service = ProjectService(db)
    stats = await project_service.get_project_stats(project_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Project not found")

    return stats


@router.post("/{project_id}/pause")
async def pause_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Pause a project."""
    project_service = ProjectService(db)
    project = await project_service.pause_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project paused", "project": ProjectResponse(**project.to_dict())}


@router.post("/{project_id}/resume")
async def resume_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused project."""
    project_service = ProjectService(db)
    project = await project_service.resume_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not paused")

    return {"message": "Project resumed", "project": ProjectResponse(**project.to_dict())}


@router.get("/{project_id}/timeline")
async def get_project_timeline(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get project timeline with events and milestones."""
    progress_service = ProgressService(db)
    timeline = await progress_service.get_project_timeline(project_id)

    if not timeline:
        raise HTTPException(status_code=404, detail="Project not found")

    return timeline


@router.get("/{project_id}/events")
async def get_project_events(
    project_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get project events/logs."""
    progress_service = ProgressService(db)
    events = await progress_service.get_project_events(
        project_id=project_id,
        limit=limit,
        offset=offset
    )

    return [e.to_dict() for e in events]


@router.get("/{project_id}/artifacts")
async def get_project_artifacts(
    project_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get project artifacts."""
    progress_service = ProgressService(db)
    artifacts = await progress_service.get_artifacts(project_id, limit)

    return [a.to_dict() for a in artifacts]


@router.websocket("/{project_id}/events/ws")
async def websocket_project_events(
    websocket: WebSocket,
    project_id: str
):
    """WebSocket endpoint for real-time project events."""
    await websocket.accept()
    logger.info("WebSocket connected", project_id=project_id)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "project_id": project_id,
            "message": "WebSocket connected"
        })

        # Keep connection alive and stream events
        # In production, implement proper event streaming from Redis/DB
        while True:
            # Wait for client messages (ping/pong)
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        logger.info("WebSocket disconnected", project_id=project_id)
