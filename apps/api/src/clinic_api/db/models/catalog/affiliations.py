from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base
from clinic_api.db.models.common import ActiveRecord


class PatientClinic(ActiveRecord, Base):
    __tablename__ = "patient_clinic"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_patient_clinic_patient",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_patient_clinic_clinic",
        ),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(primary_key=True)


class TherapistClinic(ActiveRecord, Base):
    __tablename__ = "therapist_clinic"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_therapist_clinic_therapist",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_therapist_clinic_clinic",
        ),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    therapist_id: Mapped[UUID] = mapped_column(primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(primary_key=True)
