from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.models.product import Product
from app.schemas.product import ProductCreate


async def list_products(
    session: AsyncSession, tenant: TenantContext
) -> list[Product]:
    stmt = select(Product).where(Product.tenant_id == tenant.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_product(
    session: AsyncSession,
    tenant: TenantContext,
    data: ProductCreate,
) -> Product:
    product = Product(
        tenant_id=tenant.id,
        name=data.name,
        sku=data.sku,
        unit_price=data.unit_price,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product
