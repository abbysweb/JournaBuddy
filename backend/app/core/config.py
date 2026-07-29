"""
JournaBuddy Core Settings
Loads all environment variables using Pydantic Settings for type-safe configuration.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@postgres:5432/journabuddy"

    # Redis / Celery broker
    redis_url: str = "redis://redis:6379/0"

    # MinIO Object Storage
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "journabuddy-uploads"

    # Ollama (Primary LLM)
    ollama_url: str = "http://ollama-1:11434"
    ollama_model: str = "llama3.1:8b"

    # Fallback LLM providers
    nvidia_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton settings instance used across the application
settings = Settings()
