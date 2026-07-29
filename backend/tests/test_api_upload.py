import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
import io

# Initialize the TestClient with our FastAPI app
client = TestClient(app)

def test_health_check():
    """
    Test the basic health check endpoint to ensure the API is running.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("app.api.upload.upload_pdf")
@patch("app.api.upload.extract_text_from_pdf")
def test_upload_document_success(mock_extract_text, mock_upload_pdf):
    """
    Test the /api/upload endpoint with a valid PDF file.
    We mock the MinIO upload and PDF extraction to isolate the endpoint logic.
    """
    # Setup our mocks
    mock_extract_text.return_value = "Mocked PDF text content"
    mock_upload_pdf.return_value = None  # Upload returns nothing on success
    
    # Create a dummy PDF file in memory
    dummy_pdf = io.BytesIO(b"%PDF-1.4 dummy content")
    dummy_pdf.name = "test_paper.pdf"
    
    # Send a POST request with the file
    response = client.post(
        "/api/upload", 
        files={"file": ("test_paper.pdf", dummy_pdf, "application/pdf")}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["filename"] == "test_paper.pdf"
    assert data["status"] == "received"
    
    # Verify our mocked services were called with the correct data
    mock_upload_pdf.assert_called_once()
    mock_extract_text.assert_called_once()

def test_upload_document_invalid_extension():
    """
    Test the /api/upload endpoint with a non-PDF file.
    It should return a 400 Bad Request.
    """
    # Create a dummy text file
    dummy_txt = io.BytesIO(b"Hello World")
    dummy_txt.name = "test_paper.txt"
    
    # Send a POST request with the text file
    response = client.post(
        "/api/upload", 
        files={"file": ("test_paper.txt", dummy_txt, "text/plain")}
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Only PDF files are supported."
