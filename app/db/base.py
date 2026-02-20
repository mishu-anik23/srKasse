import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TenantBase(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True)
    created_at: Mapped[DateTime] = mapped_column(server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
