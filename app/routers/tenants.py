from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.tenant import TenantCreate, TenantRead
from app.services.tenant_service import create_tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", response_model=TenantRead)
async def create_tenant_endpoint(
    payload: TenantCreate,
    session: AsyncSession = Depends(get_session),
) -> TenantRead:
    tenant = await create_tenant(session, payload)
    return TenantRead.model_validate(tenant)
