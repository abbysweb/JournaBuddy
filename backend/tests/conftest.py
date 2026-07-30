import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db

# Use an in-memory SQLite database for testing instead of Postgres
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Mock external dependencies (S3, Redis) for all tests."""
    monkeypatch.setattr("app.api.upload._get_s3_client", lambda: MockS3Client())
    monkeypatch.setattr("app.api.upload.redis_client", MockRedisClient())

class MockS3Client:
    def head_bucket(self, Bucket):
        pass
    def put_object(self, Bucket, Key, Body, ContentType):
        pass

class MockRedisClient:
    async def get(self, key):
        return None
    async def setex(self, key, time, value):
        pass
