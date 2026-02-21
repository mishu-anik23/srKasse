from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sku_maps import CATEGORY_MAP, QUANTITY_MAP, VENDOR_MAP
from app.core.tenant import TenantContext, get_tenant
from app.db.session import get_session
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import create_product, list_products

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/category-map")
async def get_category_map() -> dict:
    """Return category layout (code -> name + subcategories)."""
    return CATEGORY_MAP


@router.get("/vendor-map")
async def get_vendor_map() -> dict:
    """Return vendor (brand) layout (code -> name)."""
    return VENDOR_MAP


@router.get("/quantity-map")
async def get_quantity_map() -> dict:
    """Return quantity layout (code -> label e.g. 250g/ml)."""
    return QUANTITY_MAP


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
