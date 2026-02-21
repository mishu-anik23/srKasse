import uuid

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductCounter(Base):
    """Per-tenant SKU sequence counter for (brand, category, subcategory, quantity)."""

    __tablename__ = "product_counters"

    tenant_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    brand_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    category_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    subcategory_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    quantity_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    counter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
