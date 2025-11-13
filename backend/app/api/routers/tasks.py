"""
Tasks API router - endpoints for managing tasks.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.db import get_db
from app.models import Task
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    type: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    retry_count: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List tasks with optional project filter."""
    query = select(Task)

    if project_id:
        query = query.where(Task.project_id == project_id)

    query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return [TaskResponse(**t.to_dict()) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task by ID."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(**task.to_dict())


@router.get("/{task_id}/events")
async def get_task_events(
    task_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get events related to a specific task."""
    progress_service = ProgressService(db)
    events = await progress_service.get_task_events(task_id, limit)

    return [e.to_dict() for e in events]
