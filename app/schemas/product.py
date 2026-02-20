from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    sku: str
    unit_price: Decimal


class ProductRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    sku: str
    unit_price: Decimal

    model_config = {"from_attributes": True}
