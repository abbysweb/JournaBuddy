import os
from minio import Minio
from minio.error import S3Error
import io
import tempfile

# MinIO client setup
minio_client = None
try:
    minio_client = Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
    )
except Exception:
    minio_client = None

BUCKET_NAME = "journabuddy-uploads"
USE_MINIO = False

def initialize_storage():
    """Ensure the bucket exists on startup, otherwise fallback to local filesystem."""
    global USE_MINIO
    if minio_client:
        try:
            # Check if MinIO is responsive by running bucket_exists
            if minio_client.bucket_exists(BUCKET_NAME):
                print(f"[Storage] MinIO bucket '{BUCKET_NAME}' already exists.")
            else:
                minio_client.make_bucket(BUCKET_NAME)
                print(f"[Storage] Created MinIO bucket: {BUCKET_NAME}")
            USE_MINIO = True
        except Exception as e:
            print(f"[Storage] MinIO offline ({e}). Falling back to local filesystem storage.")
            USE_MINIO = False
    else:
        print("[Storage] MinIO client not configured. Falling back to local filesystem storage.")
        USE_MINIO = False

    if not USE_MINIO:
        local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
        os.makedirs(local_dir, exist_ok=True)

def save_file(file_id: str, file_data: bytes, content_type: str = "application/pdf"):
    """Saves a file to MinIO or local filesystem fallback."""
    if file_data[:4] != b"%PDF":
        raise ValueError("Invalid file format. Only PDF files are allowed.")
        
    object_name = f"{file_id}.pdf"
    
    if USE_MINIO:
        try:
            minio_client.put_object(
                BUCKET_NAME,
                object_name,
                data=io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return object_name
        except Exception as e:
            print(f"[Storage] MinIO put_object failed ({e}). Trying local filesystem.")
            
    # Local fallback
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads', object_name))
    with open(local_path, "wb") as f:
        f.write(file_data)
    return object_name

def get_file(object_name: str) -> bytes:
    """Retrieves a file from MinIO or local filesystem fallback."""
    if USE_MINIO:
        try:
            response = minio_client.get_object(BUCKET_NAME, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            print(f"[Storage] MinIO get_object failed ({e}). Trying local filesystem.")
            
    # Local fallback
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads', object_name))
    with open(local_path, "rb") as f:
        return f.read()

def get_file_path_for_pdf_reader(object_name: str) -> str:
    """Retrieves the file path for PDF reader from MinIO (via tempfile) or local filesystem fallback."""
    if USE_MINIO:
        try:
            tmp_path = os.path.join(tempfile.gettempdir(), object_name)
            minio_client.fget_object(BUCKET_NAME, object_name, tmp_path)
            return tmp_path
        except Exception as e:
            print(f"[Storage] MinIO fget_object failed ({e}). Trying local filesystem.")
            
    # Local fallback
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads', object_name))
    if os.path.exists(local_path):
        return local_path
    raise FileNotFoundError(f"File not found locally: {local_path}")
