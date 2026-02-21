"""
Seed products table from existing skus.db (SQLite).
Usage:
  Set SRKASSE_DB_URL and optionally SKUS_DB_PATH (default: skus.db).
  Set TENANT_ID to the tenant UUID to own the products, or leave unset to use first tenant.
  Run: python -m scripts.seed_products_from_skus_db
"""
import asyncio
import os
import sqlite3
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Load app config and DB before importing app models
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.product import Product
from app.models.product_counter import ProductCounter


SKUS_DB_PATH = os.environ.get("SKUS_DB_PATH", "skus.db")
TENANT_ID_ENV = os.environ.get("TENANT_ID")


def read_skus_from_sqlite(path: str) -> list[dict]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT human_sku, numeric_sku, brand_code, category_code, subcategory_code,
               quantity_code, product_seq, product_slug, full_product_name,
               country_code, note, barcode
        FROM skus
        ORDER BY id
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


async def get_or_create_tenant_id(session: AsyncSession) -> uuid.UUID:
    if TENANT_ID_ENV:
        return uuid.UUID(TENANT_ID_ENV)
    result = await session.execute(select(Tenant).limit(1))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise RuntimeError("No tenant found. Create a tenant first or set TENANT_ID.")
    return tenant.id


async def ensure_counter_at_least(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    brand_code: str,
    category_code: str,
    subcategory_code: str,
    quantity_code: str,
    at_least: int,
) -> None:
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
        session.add(
            ProductCounter(
                tenant_id=tenant_id,
                brand_code=brand_code,
                category_code=category_code,
                subcategory_code=subcategory_code,
                quantity_code=quantity_code,
                counter=max(1, at_least + 1),
            )
        )
    else:
        if row.counter <= at_least:
            row.counter = at_least + 1


async def run_seed() -> None:
    if not os.path.isfile(SKUS_DB_PATH):
        print(f"skus.db not found at {SKUS_DB_PATH}. Set SKUS_DB_PATH or run from repo root.")
        return
    rows = read_skus_from_sqlite(SKUS_DB_PATH)
    if not rows:
        print("No rows in skus.db.")
        return

    async with AsyncSessionLocal() as session:
        tenant_id = await get_or_create_tenant_id(session)
        print(f"Using tenant_id={tenant_id}. Importing {len(rows)} products...")

        for r in rows:
            seq_val = int(r["product_seq"]) if r["product_seq"].isdigit() else 0
            await ensure_counter_at_least(
                session,
                tenant_id,
                r["brand_code"],
                r["category_code"],
                r["subcategory_code"],
                r["quantity_code"],
                seq_val,
            )
            product = Product(
                tenant_id=tenant_id,
                human_sku=r["human_sku"],
                numeric_sku=r["numeric_sku"],
                brand_code=r["brand_code"],
                category_code=r["category_code"],
                subcategory_code=r["subcategory_code"],
                quantity_code=r["quantity_code"],
                product_seq=r["product_seq"],
                product_slug=r.get("product_slug"),
                full_product_name=r["full_product_name"] or "",
                country_code=r.get("country_code"),
                note=r.get("note"),
                barcode=r.get("barcode"),
                unit_price=None,
            )
            session.add(product)
        await session.commit()
        print(f"Imported {len(rows)} products for tenant {tenant_id}.")


def main() -> None:
    asyncio.run(run_seed())


if __name__ == "__main__":
    main()
