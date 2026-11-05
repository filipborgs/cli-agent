from datetime import date, datetime, time
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class PatientAvailability(Base):
    __tablename__ = "patient_availability"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_patient_availability_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_patient_availability_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_patient_availability_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_patient_availability_patient",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_patient_availability_validity",
        ),
        sa.CheckConstraint(
            "weekday BETWEEN 0 AND 6", name="ck_patient_availability_weekday"
        ),
        sa.CheckConstraint(
            "start_time < end_time", name="ck_patient_availability_window"
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
    patient_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    weekday: Mapped[int] = mapped_column(sa.SmallInteger(), nullable=False)
    start_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    valid_from: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)


class TherapistAvailability(Base):
    __tablename__ = "therapist_availability"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_therapist_availability_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_therapist_availability_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_therapist_availability_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_therapist_availability_therapist",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_therapist_availability_validity",
        ),
        sa.CheckConstraint(
            "weekday BETWEEN 0 AND 6", name="ck_therapist_availability_weekday"
        ),
        sa.CheckConstraint(
            "start_time < end_time", name="ck_therapist_availability_window"
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
    therapist_id: Mapped[UUID] = mapped_column(sa.Uuid(), nullable=False)
    weekday: Mapped[int] = mapped_column(sa.SmallInteger(), nullable=False)
    start_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    valid_from: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)


class ClinicHours(Base):
    __tablename__ = "clinic_hours"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_clinic_hours_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_clinic_hours_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_clinic_hours_clinic",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_clinic_hours_validity",
        ),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_clinic_hours_weekday"),
        sa.CheckConstraint("start_time < end_time", name="ck_clinic_hours_window"),
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
    weekday: Mapped[int] = mapped_column(sa.SmallInteger(), nullable=False)
    start_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    valid_from: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)
