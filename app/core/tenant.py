from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.security import decode_access_token
from app.schemas.auth import TokenPayload


class TenantContext:
    def __init__(self, tenant_id: UUID):
        self.id = tenant_id


async def get_current_user(request: Request) -> TokenPayload:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    email = payload.get("email")
    if not sub or not tenant_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return TokenPayload(sub=UUID(sub), tenant_id=UUID(tenant_id), email=email)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_tenant(
    user: TokenPayload = Depends(get_current_user),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> TenantContext:
    tenant_id = user.tenant_id
    if x_tenant_id and x_tenant_id != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch",
        )
    return TenantContext(tenant_id)
