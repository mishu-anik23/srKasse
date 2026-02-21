from decimal import Decimal

from sqlalchemy import Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase


class Product(TenantBase):
    """Product aligned with skus.db schema; tenant-scoped."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "human_sku", name="uq_products_tenant_human_sku"
        ),
    )

    # skus.db schema fields
    human_sku: Mapped[str] = mapped_column(String(64), index=True)
    numeric_sku: Mapped[str] = mapped_column(String(32), index=True)
    brand_code: Mapped[str] = mapped_column(String(8), nullable=False)
    category_code: Mapped[str] = mapped_column(String(8), nullable=False)
    subcategory_code: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity_code: Mapped[str] = mapped_column(String(8), nullable=False)
    product_seq: Mapped[str] = mapped_column(String(8), nullable=False)
    product_slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Optional pricing (app-specific)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2), nullable=True
    )
