# srKasse API

Multi-tenant FastAPI backend for **Sunrise Supermarket** (srKasse). Single-DB tenancy via `tenant_id`, JWT auth, async SQLAlchemy, PostgreSQL.

![Sunrise Supermarket logo](app/static/logo.png)

## Stack

- FastAPI, async SQLAlchemy, PostgreSQL (asyncpg)
- JWT auth with `tenant_id` in token payload
- Alembic migrations

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .
cp .env.example .env     # edit .env with your DB URL and secret
alembic upgrade head
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  
- Logo/branding: http://127.0.0.1:8000/static/logo.png  

## Tenancy

- Each user belongs to one tenant (`tenant_id` in JWT).
- Optional `X-Tenant-Id` header must match token; otherwise 403.
- Data (e.g. products) is scoped by `tenant_id`.

## Products (SKU schema)

Products follow the **skus.db** layout from `sr-sku-gen.py`:

- **Attributes:** `human_sku`, `numeric_sku`, `brand_code`, `category_code`, `subcategory_code`, `quantity_code`, `product_seq`, `product_slug`, `full_product_name`, `country_code`, `note`, `barcode`, optional `unit_price`.
- **Lookup maps** (category layout, vendor/brand, quantity) are in `app/core/sku_maps.py` and exposed as:
  - `GET /api/products/category-map`
  - `GET /api/products/vendor-map`
  - `GET /api/products/quantity-map`
- Create product: `POST /api/products/` with `brand_code`, `category_code`, `subcategory_code`, `quantity_code`, `full_product_name` (and optional `country_code`, `note`, `barcode`, `unit_price`). Human/numeric SKU and sequence are generated per tenant.

### Seed products from skus.db

To fill the app DB with products from an existing **skus.db** (e.g. from the sr-sku-gen GUI):

```bash
set SKUS_DB_PATH=skus.db    # optional; default skus.db
set TENANT_ID=<uuid>         # optional; uses first tenant if unset
python -m scripts.seed_products_from_skus_db
```

Run from the project root so `SKUS_DB_PATH` resolves and the app can load `.env` for `SRKASSE_DB_URL`.

## License

Proprietary – Sunrise Supermarket.
