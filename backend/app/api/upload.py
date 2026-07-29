import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import ClientError
from app.services.pdf_extractor import extract_text_from_pdf

router = APIRouter()

# Initialize MinIO client
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "journabuddy-uploads"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1"
    )

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    task_id = str(uuid.uuid4())
    object_name = f"{task_id}_{file.filename}"
    
    s3_client = get_s3_client()
    
    try:
        # Create bucket if it doesn't exist
        try:
            s3_client.head_bucket(Bucket=BUCKET_NAME)
        except ClientError:
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            
        # Read file and upload to MinIO
        file_content = await file.read()
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=object_name,
            Body=file_content,
            ContentType="application/pdf"
        )
        
        # Optionally, save to local disk temporarily for extraction
        temp_path = f"/tmp/{object_name}"
        with open(temp_path, "wb") as f:
            f.write(file_content)
            
        # Extract text (simulating Phase 1 extraction step)
        extracted_text = extract_text_from_pdf(temp_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {
            "task_id": task_id,
            "filename": file.filename,
            "status": "success",
            "message": "File uploaded and processed successfully",
            "extracted_length": len(extracted_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
