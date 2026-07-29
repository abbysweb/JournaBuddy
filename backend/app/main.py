from fastapi import FastAPI
from app.api import upload

app = FastAPI(
    title="JournaBuddy API",
    description="Research Paper Intelligence Platform",
    version="0.1.0"
)

# Include routers
app.include_router(upload.router, prefix="/api")

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}
