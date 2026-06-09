import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override database BEFORE importing app
import database
test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
test_session = async_sessionmaker(test_engine, expire_on_commit=False)

async def override_get_db():
    async with test_session() as session:
        yield session

# Set environment variables before importing app
import os
os.environ["ADMIN_SECRET"] = "test_secret_key_for_testing_only_32chars!"
os.environ["ADMIN_PASS"] = "admin888"
os.environ["ADMIN_USER"] = "admin"
os.environ["TESTING"] = "1"
os.environ["LOGIN_RATE_LIMIT"] = "1000/minute"

from app import app
from database import Base
import models  # noqa: F401 - ensure models are registered
from models import AuditLog  # noqa: F401 - register audit model

app.dependency_overrides[database.get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Get authenticated headers for admin endpoints."""
    r = await client.post("/api/admin/login", json={"username": "admin", "password": "admin888"})
    assert r.status_code == 200
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}
