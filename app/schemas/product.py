from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Create product: codes from category/vendor/quantity maps; name required."""

    brand_code: str = Field(..., min_length=1, max_length=8)
    category_code: str = Field(..., min_length=1, max_length=8)
    subcategory_code: str = Field(..., min_length=1, max_length=8)
    quantity_code: str = Field(..., min_length=1, max_length=8)
    full_product_name: str = Field(..., min_length=1, max_length=255)
    country_code: str | None = Field(None, max_length=16)
    note: str | None = Field(None, max_length=512)
    barcode: str | None = Field(None, max_length=64)
    unit_price: Decimal | None = None


class ProductRead(BaseModel):
    id: UUID
    tenant_id: UUID
    human_sku: str
    numeric_sku: str
    brand_code: str
    category_code: str
    subcategory_code: str
    quantity_code: str
    product_seq: str
    product_slug: str | None
    full_product_name: str
    country_code: str | None
    note: str | None
    barcode: str | None
    unit_price: Decimal | None

    model_config = {"from_attributes": True}
