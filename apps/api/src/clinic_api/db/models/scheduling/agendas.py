from datetime import date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class MonthlyAgenda(Base):
    __tablename__ = "monthly_agenda"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_monthly_agenda_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_monthly_agenda_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_monthly_agenda_clinic",
        ),
        sa.CheckConstraint(
            "EXTRACT(DAY FROM month) = 1", name="ck_monthly_agenda_month"
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "clinic_id",
            "month",
            name="uq_monthly_agenda_tenant_id_clinic_id_month",
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
    month: Mapped[date] = mapped_column(sa.Date(), nullable=False)


class GenerationRun(Base):
    __tablename__ = "generation_run"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_generation_run_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_generation_run_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "monthly_agenda_id"],
            ["monthly_agenda.tenant_id", "monthly_agenda.id"],
            name="fk_generation_run_monthly_agenda",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'partial', 'failed')",
            name="ck_generation_run_status",
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_generation_run_times",
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
    monthly_agenda_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'running'")
    )
    parameters: Mapped[dict[str, object]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )


class GenerationDeficit(Base):
    __tablename__ = "generation_deficit"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_generation_deficit_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_generation_deficit_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "generation_run_id"],
            ["generation_run.tenant_id", "generation_run.id"],
            name="fk_generation_deficit_generation_run",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_generation_deficit_treatment_plan",
        ),
        sa.CheckConstraint("missing_count > 0", name="ck_generation_deficit_missing"),
        sa.CheckConstraint(
            "EXTRACT(ISODOW FROM week_start) = 1", name="ck_generation_deficit_week"
        ),
        sa.CheckConstraint(
            "reason_code IN ('no_common_availability', 'no_compatible_room', 'resource_conflict')",
            name="ck_generation_deficit_reason_code",
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
    generation_run_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    treatment_plan_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    week_start: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    missing_count: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    reason_code: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )
