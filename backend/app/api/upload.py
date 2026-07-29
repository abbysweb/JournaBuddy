"""
JournaBuddy Upload API Router
Handles PDF file ingestion, MinIO storage, task DB record creation,
and Celery pipeline dispatch.

Endpoints:
  POST /api/upload — Upload a PDF for analysis
"""
import os
import uuid
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.config import settings
from app.db.session import get_db
from app.schemas.schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Maximum allowed upload size: 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024


def _get_s3_client():
    """Create a boto3 S3 client connected to MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
    )


def _ensure_bucket(s3_client) -> None:
    """Create the MinIO bucket if it does not yet exist."""
    try:
        s3_client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        s3_client.create_bucket(Bucket=settings.minio_bucket)
        logger.info(f"Created MinIO bucket: {settings.minio_bucket}")


@router.post("/upload", response_model=UploadResponse, summary="Upload PDF for Analysis")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF manuscript for AI analysis.

    - Validates file type (PDF only) and size (≤ 50 MB)
    - Stores the file in MinIO object storage
    - Creates a Task record in PostgreSQL
    - Dispatches the extract_pdf_task to the Celery io_bound worker queue
    - Returns the task_id immediately (pipeline runs asynchronously)

    Args:
        file: Multipart PDF file upload.
        db: Async SQLAlchemy session (injected by FastAPI).

    Returns:
        UploadResponse with task_id and status "queued".
    """
    from app.models.models import Task
    from app.worker.tasks import extract_pdf_task

    # ── Validate file type ──
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error_code": "INVALID_FILE_TYPE",
                "message": "Only PDF files are accepted.",
            },
        )

    # ── Read file and validate size ──
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={
                "status": "error",
                "error_code": "FILE_TOO_LARGE",
                "message": f"File exceeds maximum allowed size of 50 MB.",
            },
        )

    task_id = str(uuid.uuid4())
    object_key = f"{task_id}/{file.filename}"

    # ── Upload to MinIO ──
    try:
        s3 = _get_s3_client()
        _ensure_bucket(s3)
        s3.put_object(
            Bucket=settings.minio_bucket,
            Key=object_key,
            Body=file_content,
            ContentType="application/pdf",
        )
        logger.info(f"Uploaded PDF to MinIO: {object_key}")
    except Exception as e:
        logger.error(f"MinIO upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "STORAGE_ERROR",
                "message": f"Failed to store file: {str(e)}",
            },
        )

    # ── Create Task row in PostgreSQL ──
    try:
        task_row = Task(
            id=uuid.UUID(task_id),
            filename=file.filename,
            minio_object_key=object_key,
            status="queued",
            progress_percent=0,
        )
        db.add(task_row)
        await db.commit()
        logger.info(f"Created task record: {task_id}")
    except Exception as e:
        logger.error(f"DB task creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "DB_ERROR",
                "message": "Failed to create task record.",
            },
        )

    # ── Dispatch Celery pipeline task ──
    try:
        extract_pdf_task.apply_async(
            kwargs={"task_id": task_id, "object_key": object_key},
            queue="io_bound",
        )
        logger.info(f"Dispatched extract_pdf_task for task {task_id}")
    except Exception as e:
        logger.error(f"Celery dispatch failed: {e}")
        # Non-fatal: task is in DB, can be retried manually

    return UploadResponse(
        task_id=task_id,
        filename=file.filename,
        status="queued",
        message="PDF uploaded successfully. Analysis pipeline is running.",
    )
