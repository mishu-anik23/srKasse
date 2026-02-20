from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext, get_tenant
from app.db.session import get_session
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import create_product, list_products

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
async def get_products(
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_tenant),
) -> list[ProductRead]:
    products = await list_products(session, tenant)
    return [ProductRead.model_validate(p) for p in products]


@router.post("/", response_model=ProductRead)
async def post_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_tenant),
) -> ProductRead:
    product = await create_product(session, tenant, payload)
    return ProductRead.model_validate(product)
