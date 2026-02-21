"""Products: skus.db schema + product_counters.

Revision ID: 002
Revises: 001
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new SKU columns to products (nullable first for backfill)
    op.add_column(
        "products",
        sa.Column("human_sku", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("numeric_sku", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("brand_code", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("category_code", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("subcategory_code", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("quantity_code", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("product_seq", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("product_slug", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("full_product_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("country_code", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("note", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("barcode", sa.String(length=64), nullable=True),
    )

    # Backfill from legacy name/sku if present
    op.execute("""
        UPDATE products
        SET full_product_name = COALESCE(name, ''),
            human_sku = COALESCE(sku, ''),
            numeric_sku = COALESCE(sku, ''),
            brand_code = '000',
            category_code = '00',
            subcategory_code = '0',
            quantity_code = '0',
            product_seq = '01'
        WHERE full_product_name IS NULL
    """)

    # Make new columns non-nullable where required
    op.alter_column(
        "products", "human_sku",
        existing_type=sa.String(64), nullable=False,
    )
    op.alter_column(
        "products", "numeric_sku",
        existing_type=sa.String(32), nullable=False,
    )
    op.alter_column(
        "products", "brand_code",
        existing_type=sa.String(8), nullable=False,
    )
    op.alter_column(
        "products", "category_code",
        existing_type=sa.String(8), nullable=False,
    )
    op.alter_column(
        "products", "subcategory_code",
        existing_type=sa.String(8), nullable=False,
    )
    op.alter_column(
        "products", "quantity_code",
        existing_type=sa.String(8), nullable=False,
    )
    op.alter_column(
        "products", "product_seq",
        existing_type=sa.String(8), nullable=False,
    )
    op.alter_column(
        "products", "full_product_name",
        existing_type=sa.String(255), nullable=False,
    )

    # Make unit_price nullable
    op.alter_column(
        "products", "unit_price",
        existing_type=sa.Numeric(precision=12, scale=2),
        nullable=True,
    )

    # Drop legacy columns
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_column("products", "sku")
    op.drop_column("products", "name")

    # Unique constraint tenant + human_sku; indexes
    op.create_index(
        op.f("ix_products_human_sku"), "products", ["human_sku"], unique=False
    )
    op.create_index(
        op.f("ix_products_numeric_sku"), "products", ["numeric_sku"], unique=False
    )
    op.create_unique_constraint(
        "uq_products_tenant_human_sku",
        "products",
        ["tenant_id", "human_sku"],
    )

    # product_counters table
    op.create_table(
        "product_counters",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_code", sa.String(length=8), nullable=False),
        sa.Column("category_code", sa.String(length=8), nullable=False),
        sa.Column("subcategory_code", sa.String(length=8), nullable=False),
        sa.Column("quantity_code", sa.String(length=8), nullable=False),
        sa.Column("counter", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint(
            "tenant_id",
            "brand_code",
            "category_code",
            "subcategory_code",
            "quantity_code",
        ),
    )


def downgrade() -> None:
    op.drop_table("product_counters")
    op.drop_constraint(
        "uq_products_tenant_human_sku", "products", type_="unique"
    )
    op.drop_index(op.f("ix_products_numeric_sku"), table_name="products")
    op.drop_index(op.f("ix_products_human_sku"), table_name="products")
    op.add_column(
        "products",
        sa.Column("name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("sku", sa.String(length=64), nullable=True),
    )
    op.execute("UPDATE products SET name = full_product_name, sku = human_sku")
    op.alter_column(
        "products", "name",
        existing_type=sa.String(255), nullable=False,
    )
    op.alter_column(
        "products", "sku",
        existing_type=sa.String(64), nullable=False,
    )
    op.alter_column(
        "products", "unit_price",
        existing_type=sa.Numeric(precision=12, scale=2),
        nullable=False,
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=False)
    op.drop_column("products", "barcode")
    op.drop_column("products", "note")
    op.drop_column("products", "country_code")
    op.drop_column("products", "full_product_name")
    op.drop_column("products", "product_slug")
    op.drop_column("products", "product_seq")
    op.drop_column("products", "quantity_code")
    op.drop_column("products", "subcategory_code")
    op.drop_column("products", "category_code")
    op.drop_column("products", "brand_code")
    op.drop_column("products", "numeric_sku")
    op.drop_column("products", "human_sku")
