from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class ClinicClosure(Base):
    __tablename__ = "clinic_closure"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_clinic_closure_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_clinic_closure_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_clinic_closure_clinic",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_clinic_closure_interval"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_clinic_closure_user_tenant",
        ),
        sa.Index(
            "ix_clinic_closure_interval",
            "tenant_id",
            sa.text("tstzrange(starts_at, ends_at, '[)')"),
            postgresql_using="gist",
        ),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid(), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    clinic_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    reason: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    created_by: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
