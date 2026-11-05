from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class UserTenant(Base):
    __tablename__ = "user_tenant"
    __table_args__ = (
        CheckConstraint("role = 'admin'", name="ck_user_tenants_admin_role"),
    )

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    role: Mapped[str] = mapped_column(Text, server_default=text("'admin'"))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
