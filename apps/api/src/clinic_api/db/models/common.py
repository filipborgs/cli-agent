"""Column contracts shared by persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class ActiveRecord(Timestamps):
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class TenantEntity(Timestamps):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"))


class CatalogEntity(TenantEntity):
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
