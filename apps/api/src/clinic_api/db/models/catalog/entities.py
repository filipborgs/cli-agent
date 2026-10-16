from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class Clinic(Base):
    __tablename__ = "clinic"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"))
    name: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text)
    default_duration_minutes: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean)


class Patient(Base):
    __tablename__ = "patient"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"))
    name: Mapped[str]
    active: Mapped[bool] = mapped_column(Boolean)


class PatientClinic(Base):
    __tablename__ = "patient_clinic"
    tenant_id: Mapped[UUID] = mapped_column(primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patient.id"), primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinic.id"), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean)


class Therapist(Base):
    __tablename__ = "therapist"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"))
    name: Mapped[str]
    active: Mapped[bool] = mapped_column(Boolean)


class Specialty(Base):
    __tablename__ = "specialty"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"))
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean)


class Room(Base):
    __tablename__ = "room"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"))
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinic.id"))
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean)
