from datetime import date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class Appointment(Base):
    __tablename__ = "appointment"
    __table_args__ = (
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "treatment_plan_id",
            "origin",
            name="uq_appointment_origin_identity",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_appointment_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_appointment_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_appointment_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_appointment_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["room.tenant_id", "room.id"],
            name="fk_appointment_room",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_appointment_patient",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_appointment_therapist",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "specialty_id"],
            ["specialty.tenant_id", "specialty.id"],
            name="fk_appointment_specialty",
        ),
        sa.ForeignKeyConstraint(
            [
                "tenant_id",
                "treatment_plan_id",
                "patient_id",
                "therapist_id",
                "specialty_id",
            ],
            [
                "treatment_plan.tenant_id",
                "treatment_plan.id",
                "treatment_plan.patient_id",
                "treatment_plan.therapist_id",
                "treatment_plan.specialty_id",
            ],
            name="fk_appointment_plan_identity",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id", "room_id"],
            ["room.tenant_id", "room.clinic_id", "room.id"],
            name="fk_appointment_room_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id", "clinic_id"],
            [
                "treatment_plan_clinic.tenant_id",
                "treatment_plan_clinic.treatment_plan_id",
                "treatment_plan_clinic.clinic_id",
            ],
            name="fk_appointment_treatment_plan_clinic",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_appointment_interval"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_appointment_duration"),
        sa.CheckConstraint(
            "origin IN ('routine', 'replacement')", name="ck_appointment_origin"
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled', 'patient_absent', 'therapist_absent', 'dispensed')",
            name="ck_appointment_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "weekly_slot_id"],
            ["weekly_slot.tenant_id", "weekly_slot.id"],
            name="fk_appointment_weekly_slot",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "weekly_slot_id", "treatment_plan_id"],
            [
                "weekly_slot.tenant_id",
                "weekly_slot.id",
                "weekly_slot.treatment_plan_id",
            ],
            name="fk_appointment_slot_plan",
        ),
        sa.CheckConstraint(
            "replacement_decision IN ('not_applicable', 'awaiting_decision', 'granted', 'denied')",
            name="ck_appointment_replacement_decision",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "treatment_plan_id",
            name="uq_appointment_tenant_id_id_treatment_plan_id",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("patient_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status IN ('scheduled', 'completed')"),
            name="ex_appointment_patient",
            using="gist",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("therapist_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status IN ('scheduled', 'completed')"),
            name="ex_appointment_therapist",
            using="gist",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("room_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status IN ('scheduled', 'completed')"),
            name="ex_appointment_room",
            using="gist",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "replacement_due_id", "treatment_plan_id"],
            [
                "replacement_due.tenant_id",
                "replacement_due.id",
                "replacement_due.treatment_plan_id",
            ],
            name="fk_appointment_replacement",
            use_alter=True,
        ),
        sa.CheckConstraint(
            "(origin = 'routine' AND weekly_slot_id IS NOT NULL AND occurrence_date IS NOT NULL AND replacement_due_id IS NULL) OR (origin = 'replacement' AND weekly_slot_id IS NULL AND occurrence_date IS NULL AND replacement_due_id IS NOT NULL)",
            name="ck_appointment_origin_fields",
        ),
        sa.Index(
            "uq_appointment_occurrence",
            "tenant_id",
            "weekly_slot_id",
            "occurrence_date",
            unique=True,
            postgresql_where=sa.text("weekly_slot_id IS NOT NULL"),
        ),
        sa.Index(
            "uq_appointment_due_scheduled",
            "tenant_id",
            "replacement_due_id",
            unique=True,
            postgresql_where=sa.text("origin = 'replacement' AND status = 'scheduled'"),
        ),
        sa.Index(
            "uq_appointment_due_completed",
            "tenant_id",
            "replacement_due_id",
            unique=True,
            postgresql_where=sa.text("origin = 'replacement' AND status = 'completed'"),
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
    treatment_plan_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    room_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    therapist_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    specialty_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    origin: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'scheduled'")
    )
    weekly_slot_id: Mapped[UUID | None] = mapped_column(sa.Uuid(), nullable=True)
    occurrence_date: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)
    manually_adjusted: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("false")
    )
    replacement_decision: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'not_applicable'")
    )
    replacement_due_id: Mapped[UUID | None] = mapped_column(sa.Uuid(), nullable=True)


class AppointmentEvent(Base):
    __tablename__ = "appointment_event"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_appointment_event_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_appointment_event_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "appointment_id"],
            ["appointment.tenant_id", "appointment.id"],
            name="fk_appointment_event_appointment",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_appointment_event_user_tenant",
        ),
    )
    id: Mapped[UUID] = mapped_column(sa.Uuid(), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    appointment_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(sa.Uuid(), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    kind: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    before: Mapped[dict[str, object]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    after: Mapped[dict[str, object]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )
