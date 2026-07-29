import io
from minio import Minio
from app.core.config import settings

# Initialize MinIO client
s3_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

def ensure_bucket_exists():
    """Ensure the uploads bucket exists in MinIO."""
    found = s3_client.bucket_exists(settings.MINIO_BUCKET_NAME)
    if not found:
        s3_client.make_bucket(settings.MINIO_BUCKET_NAME)

def upload_pdf(task_id: str, file_data: bytes):
    """Uploads a PDF to MinIO."""
    ensure_bucket_exists()
    
    file_stream = io.BytesIO(file_data)
    file_length = len(file_data)
    
    s3_client.put_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=f"tasks/{task_id}/original.pdf",
        data=file_stream,
        length=file_length,
        content_type="application/pdf"
    )
