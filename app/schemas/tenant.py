from uuid import UUID

from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str


class TenantRead(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}
