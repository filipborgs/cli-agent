from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class PersonBlock(Base):
    __tablename__ = "person_block"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_person_block_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_person_block_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_person_block_patient",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_person_block_therapist",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_person_block_interval"),
        sa.CheckConstraint(
            "(patient_id IS NOT NULL) <> (therapist_id IS NOT NULL)",
            name="ck_person_block_one_person",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_person_block_user_tenant",
        ),
        sa.Index(
            "ix_person_block_interval",
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
    patient_id: Mapped[UUID | None] = mapped_column(sa.Uuid(), nullable=True)
    therapist_id: Mapped[UUID | None] = mapped_column(sa.Uuid(), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    reason: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    created_by: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
