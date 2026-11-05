from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class ReplacementDue(Base):
    __tablename__ = "replacement_due"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_replacement_due_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_replacement_due_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "original_appointment_id"],
            ["appointment.tenant_id", "appointment.id"],
            name="fk_replacement_due_appointment",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_replacement_due_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            [
                "tenant_id",
                "original_appointment_id",
                "treatment_plan_id",
                "original_origin",
            ],
            [
                "appointment.tenant_id",
                "appointment.id",
                "appointment.treatment_plan_id",
                "appointment.origin",
            ],
            name="fk_replacement_due_original_plan",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "original_appointment_id",
            name="uq_replacement_due_tenant_id_original_appointment_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "treatment_plan_id",
            name="uq_replacement_due_tenant_id_id_treatment_plan_id",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'scheduled', 'completed', 'closed')",
            name="ck_replacement_due_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "decided_by"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_replacement_due_user_tenant",
        ),
        sa.CheckConstraint(
            "(decided_by IS NULL) = (decided_at IS NULL)",
            name="ck_replacement_due_decision",
        ),
        sa.CheckConstraint(
            "status <> 'closed' OR (closed_reason IS NOT NULL AND length(trim(closed_reason)) > 0 AND decided_by IS NOT NULL)",
            name="ck_replacement_due_closure",
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
    original_origin: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("'routine'", persisted=True), nullable=False
    )
    original_appointment_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    treatment_plan_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    reason: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'pending'")
    )
    decided_by: Mapped[UUID | None] = mapped_column(sa.Uuid(), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    closed_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
