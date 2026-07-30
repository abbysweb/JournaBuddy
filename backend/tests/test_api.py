import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_upload_non_pdf(client):
    # Upload a dummy txt file
    files = {"file": ("test.txt", b"This is a text file", "text/plain")}
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_FILE_TYPE"

@pytest.mark.asyncio
async def test_upload_too_large(client):
    # Create a dummy file larger than 50MB
    # We don't actually need to create 50MB in memory, we can just send a mock
    # Wait, FastAPI actually reads it. Sending 51MB in memory might be slow in a test.
    # For now, let's just make a 50MB + 1 byte file in memory.
    large_content = b"0" * (50 * 1024 * 1024 + 1)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 413
    data = response.json()
    assert data["detail"]["error_code"] == "FILE_TOO_LARGE"
