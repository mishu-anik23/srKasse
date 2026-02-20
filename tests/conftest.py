import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set test env before importing app
os.environ.setdefault("SRKASSE_DB_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SRKASSE_SECRET_KEY", "test-secret-key-for-tests-only")

from app.main import app
from app.db.base import Base
from app.db.session import get_session
from app.core.tenant import get_tenant, get_current_user
from app.schemas.auth import TokenPayload


# In-memory SQLite for tests (no tenant_id FK enforcement in SQLite - tests still validate isolation in app logic)
TEST_DB = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    TEST_DB,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def override_get_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def db_session() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def app_client(db_session: AsyncSession):
    async def _get_session():
        yield db_session

    app.dependency_overrides[get_session] = _get_session
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# Sync client for simple tests that don't need async DB
@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def tenant_a_id():
    return uuid4()


@pytest.fixture
def tenant_b_id():
    return uuid4()


@pytest.fixture
def token_payload_a(tenant_a_id):
    return TokenPayload(sub=uuid4(), tenant_id=tenant_a_id, email="a@test.local")


@pytest.fixture
def token_payload_b(tenant_b_id):
    return TokenPayload(sub=uuid4(), tenant_id=tenant_b_id, email="b@test.local")
