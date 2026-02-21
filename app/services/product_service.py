import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.models.product import Product
from app.models.product_counter import ProductCounter
from app.schemas.product import ProductCreate


def _format_human_sku(
    brand_code: str,
    category_code: str,
    subcategory_code: str,
    quantity_code: str,
    product_seq: str,
) -> str:
    return f"{brand_code}-{category_code}-{subcategory_code}-{quantity_code}-{product_seq}"


def _format_numeric_sku(
    brand_code: str,
    category_code: str,
    subcategory_code: str,
    quantity_code: str,
    product_seq: str,
) -> str:
    return f"{brand_code}{category_code}{subcategory_code}{quantity_code}{product_seq}"


def _slug_from_name(name: str) -> str:
    return "".join(
        c.lower() if c.isalnum() else "-" for c in name
    ).strip("-")


async def get_next_sequence(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    brand_code: str,
    category_code: str,
    subcategory_code: str,
    quantity_code: str,
) -> int:
    """Get and increment the next product sequence for this (tenant, brand, category, subcategory, quantity)."""
    stmt = select(ProductCounter).where(
        ProductCounter.tenant_id == tenant_id,
        ProductCounter.brand_code == brand_code,
        ProductCounter.category_code == category_code,
        ProductCounter.subcategory_code == subcategory_code,
        ProductCounter.quantity_code == quantity_code,
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        row = ProductCounter(
            tenant_id=tenant_id,
            brand_code=brand_code,
            category_code=category_code,
            subcategory_code=subcategory_code,
            quantity_code=quantity_code,
            counter=1,
        )
        session.add(row)
        await session.flush()
        return 1
    next_val = row.counter + 1
    row.counter = next_val
    await session.flush()
    return next_val


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
    brand_code = data.brand_code.zfill(3)
    category_code = data.category_code.zfill(2)
    subcategory_code = (
        data.subcategory_code[-1]
        if len(data.subcategory_code) > 0
        else "0"
    )
    quantity_code = (
        data.quantity_code[-1]
        if len(data.quantity_code) > 0
        else "0"
    )

    seq = await get_next_sequence(
        session,
        tenant.id,
        brand_code,
        category_code,
        subcategory_code,
        quantity_code,
    )
    product_seq = str(seq).zfill(2)

    human_sku = _format_human_sku(
        brand_code, category_code, subcategory_code, quantity_code, product_seq
    )
    numeric_sku = _format_numeric_sku(
        brand_code, category_code, subcategory_code, quantity_code, product_seq
    )
    product_slug = _slug_from_name(data.full_product_name)

    product = Product(
        tenant_id=tenant.id,
        human_sku=human_sku,
        numeric_sku=numeric_sku,
        brand_code=brand_code,
        category_code=category_code,
        subcategory_code=subcategory_code,
        quantity_code=quantity_code,
        product_seq=product_seq,
        product_slug=product_slug,
        full_product_name=data.full_product_name,
        country_code=data.country_code,
        note=data.note,
        barcode=data.barcode,
        unit_price=data.unit_price,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product
