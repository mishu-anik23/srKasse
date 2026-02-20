<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Draft a minimal srKasse FastAPI repo layout (files + content outlines) ready to paste into Cursor

Below is a **minimal srKasse FastAPI repo layout** with file tree and concise content outlines, aligned with: FastAPI, async SQLAlchemy, PostgreSQL, JWT auth, and **single-DB multi-tenancy via tenant_id**. You can paste this into Cursor as a starting blueprint.[^1][^2][^3]

***

## 1. Repository Structure

```text
srkasse/
  pyproject.toml
  alembic.ini
  .env.example
  README.md

  app/
    main.py

    core/
      config.py
      security.py
      tenant.py

    db/
      session.py
      base.py
      init_db.py

    models/
      __init__.py
      tenant.py
      user.py
      product.py

    schemas/
      __init__.py
      tenant.py
      user.py
      product.py
      auth.py

    services/
      __init__.py
      tenant_service.py
      user_service.py
      product_service.py

    routers/
      __init__.py
      auth.py
      tenants.py
      users.py
      products.py

    tests/
      __init__.py
      test_health.py
      test_multitenant_products.py
```

You will add further domains (inventory, POS, builder) later, but this is a clean MVP skeleton.[^2][^3]

***

## 2. Top-level files

### `pyproject.toml`

Outline:

- Project metadata and dependencies:

```toml
[project]
name = "srkasse"
version = "0.1.0"
dependencies = [
  "fastapi[all]",
  "uvicorn[standard]",
  "sqlalchemy[asyncio]",
  "asyncpg",
  "alembic",
  "python-jose[cryptography]",
  "passlib[bcrypt]",
  "pydantic[email]",
]

[tool.black]
line-length = 88
```


### `.env.example`

```bash
SRKASSE_DB_URL=postgresql+asyncpg://srkasse:srkasse@localhost:5432/srkasse
SRKASSE_SECRET_KEY=change_me
SRKASSE_ACCESS_TOKEN_EXPIRE_MINUTES=60
SRKASSE_ALGORITHM=HS256
```


***

## 3. `app/main.py`

FastAPI app factory and router includes:

```python
from fastapi import FastAPI
from app.db.session import init_engine
from app.routers import auth, tenants, users, products

def create_app() -> FastAPI:
    app = FastAPI(title="srKasse API")

    init_engine()

    app.include_router(auth.router, prefix="/api")
    app.include_router(tenants.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(products.router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

app = create_app()
```


***

## 4. `app/core`

### `config.py`

Central settings, loaded from env:

```python
from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    database_url: AnyUrl
    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    class Config:
        env_prefix = "SRKASSE_"
        env_file = ".env"

settings = Settings()
```


### `security.py`

JWT helpers and password hashing:

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes
    ))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
```

You’ll also define `get_current_user` here or in a separate auth helper later.

### `tenant.py`

Tenant resolution via JWT claim + header guard.[^1][^2]

```python
from fastapi import Depends, Header, HTTPException, status
from uuid import UUID
from app.schemas.auth import TokenPayload
from app.core.security import settings  # adapt as needed

class TenantContext:
    def __init__(self, tenant_id: UUID):
        self.id = tenant_id

async def get_current_user() -> TokenPayload:
    # Outline only: parse JWT from Authorization header, validate, return payload
    ...

async def get_tenant(
    user: TokenPayload = Depends(get_current_user),
    x_tenant_id: str | None = Header(default=None),
) -> TenantContext:
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not found in token",
        )

    if x_tenant_id and x_tenant_id != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch",
        )

    return TenantContext(tenant_id)
```


***

## 5. `app/db`

### `session.py`

Async engine \& session, plus init hook.[^3][^4]

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def init_engine():
    # placeholder; can extend later for startup hooks
    pass

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```


### `base.py`

Declarative Base + TenantBase.[^3][^1]

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
import uuid

class Base(DeclarativeBase):
    pass

class TenantBase(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True)
    created_at: Mapped[DateTime] = mapped_column(server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```


### `init_db.py`

Outline for creating initial tenant + admin:

```python
async def init_db():
    # create first tenant, admin user if none exist
    ...
```


***

## 6. `app/models`

### `tenant.py`

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.db.base import Base
import uuid

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
```


### `user.py`

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey
from app.db.base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)

    tenant = relationship("Tenant", backref="users")
```


### `product.py`

Tenant-scoped example:[^3]

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric
from app.db.base import TenantBase

class Product(TenantBase):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str] = mapped_column(String(64), index=True)
    unit_price: Mapped[Numeric] = mapped_column()
```


***

## 7. `app/schemas`

Define Pydantic schemas for transport.[^2][^3]

### `auth.py`

```python
from pydantic import BaseModel, EmailStr
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: UUID
    tenant_id: UUID
    email: EmailStr
```


### `tenant.py`

```python
from pydantic import BaseModel
from uuid import UUID

class TenantCreate(BaseModel):
    name: str

class TenantRead(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True
```


### `user.py`

```python
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    tenant_id: UUID

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    tenant_id: UUID

    class Config:
        from_attributes = True
```


### `product.py`

```python
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    sku: str
    unit_price: Decimal

class ProductRead(BaseModel):
    id: UUID
    name: str
    sku: str
    unit_price: Decimal

    class Config:
        from_attributes = True
```


***

## 8. `app/services`

### `tenant_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate

async def create_tenant(session: AsyncSession, data: TenantCreate) -> Tenant:
    tenant = Tenant(name=data.name)
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant

async def get_tenant_by_name(session: AsyncSession, name: str) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.name == name)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()
```


### `product_service.py`

Tenant-aware pattern:[^1][^3]

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product
from app.schemas.product import ProductCreate
from app.core.tenant import TenantContext

async def list_products(session: AsyncSession, tenant: TenantContext):
    stmt = select(Product).where(Product.tenant_id == tenant.id)
    res = await session.execute(stmt)
    return res.scalars().all()

async def create_product(
    session: AsyncSession,
    tenant: TenantContext,
    data: ProductCreate,
) -> Product:
    product = Product(
        tenant_id=tenant.id,
        name=data.name,
        sku=data.sku,
        unit_price=data.unit_price,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product
```


***

## 9. `app/routers`

### `auth.py`

Outline for login endpoint returning JWT with tenant_id:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.auth import Token
from app.core.security import create_access_token, verify_password
from app.models.user import User

router = APIRouter(tags=["auth"])

@router.post("/auth/login", response_model=Token)
async def login(...):
    # lookup user, verify password, create token with tenant_id in payload
    ...
```


### `tenants.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.tenant import TenantCreate, TenantRead
from app.services.tenant_service import create_tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/", response_model=TenantRead)
async def create_tenant_endpoint(
    payload: TenantCreate,
    session: AsyncSession = Depends(get_session),
):
    return await create_tenant(session, payload)
```


### `products.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import list_products, create_product
from app.core.tenant import get_tenant, TenantContext

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=list[ProductRead])
async def get_products(
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_tenant),
):
    return await list_products(session, tenant)

@router.post("/", response_model=ProductRead)
async def post_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_tenant),
):
    return await create_product(session, tenant, payload)
```


***

## 10. Tests

### `tests/test_health.py`

Simple smoke test:

```python
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```


### `tests/test_multitenant_products.py`

Later you’ll add a test to confirm tenant isolation by creating products in two tenants and ensuring they don’t leak.

***

You can now:

1. Paste this **structure + outlines** into a `design.md`/`project_config.md` in Cursor.
2. Ask Cursor to scaffold missing code (e.g., full JWT auth, tests, Alembic migrations) while preserving this layout and tenant pattern.[^5]

<div align="center">⁂</div>

[^1]: https://app-generator.dev/docs/technologies/fastapi/multitenancy.html

[^2]: https://www.codingeasypeasy.com/blog/build-a-multi-tenant-saas-application-with-fastapi-a-comprehensive-guide

[^3]: https://github.com/JuanNovas/Product-Inventory-Management-System

[^4]: https://testdriven.io/blog/fastapi-postgres-websockets/

[^5]: https://forum.cursor.com/t/guide-a-simpler-more-autonomous-ai-workflow-for-cursor-new-update/70688

