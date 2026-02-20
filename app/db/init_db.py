from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User


async def init_db() -> None:
    """Create first tenant and admin user if none exist."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tenant).limit(1))
        if result.scalar_one_or_none() is not None:
            return
        tenant = Tenant(name="Sunrise Supermarket")
        session.add(tenant)
        await session.flush()
        admin = User(
            email="admin@sunrise.local",
            hashed_password=hash_password("admin"),
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
