from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate


async def create_tenant(session: AsyncSession, data: TenantCreate) -> Tenant:
    tenant = Tenant(name=data.name)
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant


async def get_tenant_by_name(
    session: AsyncSession, name: str
) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
