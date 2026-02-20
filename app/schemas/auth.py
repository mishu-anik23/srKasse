from uuid import UUID

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: UUID
    tenant_id: UUID
    email: str  # EmailStr from token string


class LoginRequest(BaseModel):
    email: str
    password: str
