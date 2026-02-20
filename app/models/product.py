from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase


class Product(TenantBase):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str] = mapped_column(String(64), index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
