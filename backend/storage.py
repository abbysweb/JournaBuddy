import os
from minio import Minio
from minio.error import S3Error
import io
import tempfile

# MinIO client setup
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "minio:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
)

BUCKET_NAME = "journabuddy-uploads"

def initialize_storage():
    """Ensure the bucket exists on startup."""
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            print(f"[Storage] Created MinIO bucket: {BUCKET_NAME}")
        else:
            print(f"[Storage] MinIO bucket '{BUCKET_NAME}' already exists.")
    except Exception as e:
        print(f"[Storage] Error initializing MinIO: {e}")

def save_file(file_id: str, file_data: bytes, content_type: str = "application/pdf"):
    """Saves a file to MinIO and returns the object name."""
    object_name = f"{file_id}.pdf"
    
    # Check magic bytes for PDF validation if possible
    if file_data[:4] != b"%PDF":
        raise ValueError("Invalid file format. Only PDF files are allowed.")
        
    try:
        minio_client.put_object(
            BUCKET_NAME,
            object_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type
        )
        return object_name
    except S3Error as e:
        print(f"[Storage] Failed to upload {object_name}: {e}")
        raise e

def get_file(object_name: str) -> bytes:
    """Retrieves a file from MinIO."""
    try:
        response = minio_client.get_object(BUCKET_NAME, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        print(f"[Storage] Failed to fetch {object_name}: {e}")
        raise e

def get_file_path_for_pdf_reader(object_name: str) -> str:
    """
    Downloads the file temporarily to the local disk and returns the path.
    This is necessary because PyMuPDF (fitz) typically reads from a file path.
    """
    # Use the standard library tempfile to get a cross-platform temporary directory
    # (e.g. /tmp on Linux/Mac, or AppData/Local/Temp on Windows).
    tmp_path = os.path.join(tempfile.gettempdir(), object_name)
    try:
        minio_client.fget_object(BUCKET_NAME, object_name, tmp_path)
        return tmp_path
    except S3Error as e:
        print(f"[Storage] Failed to download {object_name} to disk: {e}")
        raise e
