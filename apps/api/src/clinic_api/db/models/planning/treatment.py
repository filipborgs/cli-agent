from datetime import date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class TreatmentPlan(Base):
    __tablename__ = "treatment_plan"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_treatment_plan_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_treatment_plan_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_treatment_plan_patient",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_treatment_plan_therapist",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "specialty_id"],
            ["specialty.tenant_id", "specialty.id"],
            name="fk_treatment_plan_specialty",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_treatment_plan_validity",
        ),
        sa.CheckConstraint("sessions_per_week > 0", name="ck_treatment_plan_frequency"),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_treatment_plan_duration",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "patient_id",
            "therapist_id",
            "specialty_id",
            name="uq_treatment_plan_identity",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("patient_id", "="),
            ("therapist_id", "="),
            ("specialty_id", "="),
            (sa.text("daterange(valid_from, valid_until + 1, '[)')"), "&&"),
            name="ex_treatment_plan_validity",
            using="gist",
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
    patient_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    therapist_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    specialty_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    sessions_per_week: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    valid_from: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)


class TreatmentPlanClinic(Base):
    __tablename__ = "treatment_plan_clinic"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_treatment_plan_clinic_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_treatment_plan_clinic_clinic",
        ),
    )
    tenant_id: Mapped[UUID] = mapped_column(sa.Uuid(), primary_key=True)
    treatment_plan_id: Mapped[UUID] = mapped_column(sa.Uuid(), primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(sa.Uuid(), primary_key=True)
    active: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
