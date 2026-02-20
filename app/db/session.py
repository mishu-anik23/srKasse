from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def init_engine() -> None:
    """Placeholder for startup hooks (e.g. run_migrations)."""
    pass


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
