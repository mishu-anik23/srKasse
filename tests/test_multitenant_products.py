"""Test tenant isolation: products created in one tenant are not visible in another."""
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.core.tenant import TenantContext, get_tenant, get_current_user
from app.db.session import get_session
from app.main import app
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import TokenPayload


@pytest.fixture
async def db_with_tenants(db_session: AsyncSession):
    """Create two tenants and two users."""
    t1 = Tenant(id=uuid4(), name="Tenant A")
    t2 = Tenant(id=uuid4(), name="Tenant B")
    db_session.add(t1)
    db_session.add(t2)
    await db_session.flush()
    u1 = User(
        id=uuid4(),
        email="user_a@test.local",
        hashed_password=hash_password("pass"),
        tenant_id=t1.id,
        is_active=True,
    )
    u2 = User(
        id=uuid4(),
        email="user_b@test.local",
        hashed_password=hash_password("pass"),
        tenant_id=t2.id,
        is_active=True,
    )
    db_session.add(u1)
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(t1)
    await db_session.refresh(t2)
    await db_session.refresh(u1)
    await db_session.refresh(u2)
    return db_session, t1, t2, u1, u2


@pytest.mark.asyncio
async def test_multitenant_products_isolation(db_with_tenants) -> None:
    db_session, t1, t2, u1, u2 = db_with_tenants

    async def get_session_override():
        yield db_session

    async def get_current_user_a():
        return TokenPayload(sub=u1.id, tenant_id=t1.id, email=u1.email)

    async def get_current_user_b():
        return TokenPayload(sub=u2.id, tenant_id=t2.id, email=u2.email)

    async def get_tenant_a():
        return TenantContext(t1.id)

    async def get_tenant_b():
        return TenantContext(t2.id)

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_a
    app.dependency_overrides[get_tenant] = get_tenant_a

    transport = ASGITransport(app=app)
    client_a = AsyncClient(transport=transport, base_url="http://test")

    # Tenant A creates a product (SKU schema: brand, category, subcategory, quantity, full_product_name)
    r = await client_a.post(
        "/api/products/",
        json={
            "brand_code": "001",
            "category_code": "01",
            "subcategory_code": "1",
            "quantity_code": "1",
            "full_product_name": "Product A1",
            "unit_price": "10.50",
        },
    )
    assert r.status_code == 200, r.text
    list_a = await client_a.get("/api/products/")
    assert list_a.status_code == 200
    products_a = list_a.json()
    assert len(products_a) == 1
    assert products_a[0]["full_product_name"] == "Product A1"
    assert "human_sku" in products_a[0]

    # Client as tenant B
    app.dependency_overrides[get_current_user] = get_current_user_b
    app.dependency_overrides[get_tenant] = get_tenant_b
    client_b = AsyncClient(transport=transport, base_url="http://test")

    # Tenant B creates a different product
    r2 = await client_b.post(
        "/api/products/",
        json={
            "brand_code": "002",
            "category_code": "02",
            "subcategory_code": "1",
            "quantity_code": "2",
            "full_product_name": "Product B1",
            "unit_price": "99.00",
        },
    )
    assert r2.status_code == 200, r2.text

    # Tenant B must not see Tenant A's product
    list_b = await client_b.get("/api/products/")
    assert list_b.status_code == 200
    products_b = list_b.json()
    assert len(products_b) == 1
    assert products_b[0]["full_product_name"] == "Product B1"
    assert all(p["full_product_name"] != "Product A1" for p in products_b)

    # Clean overrides
    app.dependency_overrides.pop(get_session, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_tenant, None)
