"""
JournaBuddy Task Status API Router
Provides endpoints for polling the analysis pipeline status of a task.

Endpoints:
  GET /api/task/{task_id} — Get full task status and analysis results
"""
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
import asyncio
import json

from app.db.session import get_db
from app.schemas.schemas import TaskStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/task/{task_id}", response_model=TaskStatusResponse, summary="Get Task Status")
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Poll the status and results of a running or completed analysis pipeline task.

    Returns task metadata including:
    - Current status (queued / processing / agents_running / completed / failed)
    - Progress percentage (0–100)
    - Dashboard payload (symbolic check results, agent outputs) as they become available

    Args:
        task_id: UUID string of the task (returned by POST /api/upload).
        db: Async SQLAlchemy session.

    Returns:
        TaskStatusResponse with current pipeline state and results.

    Raises:
        404: If no task with this ID exists.
    """
    import uuid
    from app.models.models import Task

    # Validate UUID format
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task_id format.")

    # Fetch the task from DB
    result = await db.execute(select(Task).where(Task.id == task_uuid))
    task_row = result.scalar_one_or_none()

    if not task_row:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "error_code": "TASK_NOT_FOUND",
                "message": f"No task found with id: {task_id}",
            },
        )

    return TaskStatusResponse(
        task_id=str(task_row.id),
        filename=task_row.filename,
        status=task_row.status,
        progress_percent=task_row.progress_percent,
        dashboard_payload=task_row.dashboard_payload,
        created_at=task_row.created_at.isoformat(),
    )


@router.get("/stream/{task_id}", summary="Stream Task Status via SSE")
async def stream_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream live updates of a running analysis pipeline task.
    """
    import uuid
    from app.models.models import Task

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task_id format.")

    async def event_generator():
        while True:
            # Rollback to clear transaction state and fetch fresh data
            await db.rollback()
            result = await db.execute(select(Task).where(Task.id == task_uuid))
            task_row = result.scalar_one_or_none()
            
            if not task_row:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                break

            payload = {
                "task_id": str(task_row.id),
                "status": task_row.status,
                "progress_percent": task_row.progress_percent,
                "dashboard_payload": task_row.dashboard_payload,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if task_row.status in ["completed", "failed"]:
                break

            await asyncio.sleep(1.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
