from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
from app.services.storage import upload_pdf
from app.services.pdf_extractor import extract_text_from_pdf

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    
    try:
        # Read the file data
        file_data = await file.read()
        
        # 1. Store in MinIO
        upload_pdf(task_id, file_data)
        
        # 2. Extract text (Initial parsing)
        extracted_text = extract_text_from_pdf(file_data)
        
        # Note: In Phase 2, we will send a Celery task here to process the text asynchronously.
        # For Phase 1, we just return success to the frontend.
        
        return {
            "task_id": task_id,
            "filename": file.filename,
            "status": "received",
            "message": "File uploaded and parsed successfully."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")
