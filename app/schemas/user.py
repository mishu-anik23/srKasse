from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    tenant_id: UUID


class UserRead(BaseModel):
    id: UUID
    email: str
    tenant_id: UUID

    model_config = {"from_attributes": True}
