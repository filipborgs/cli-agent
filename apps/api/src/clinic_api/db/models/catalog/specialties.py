from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base
from clinic_api.db.models.common import ActiveRecord, CatalogEntity


class Specialty(CatalogEntity, Base):
    __tablename__ = "specialty"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_specialty_tenant_id"),
        UniqueConstraint("tenant_id", "normalized_name", name="uq_specialty_name"),
    )
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)


class TherapistSpecialty(ActiveRecord, Base):
    __tablename__ = "therapist_specialty"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_therapist_specialty_therapist",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "specialty_id"],
            ["specialty.tenant_id", "specialty.id"],
            name="fk_therapist_specialty_specialty",
        ),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    therapist_id: Mapped[UUID] = mapped_column(primary_key=True)
    specialty_id: Mapped[UUID] = mapped_column(primary_key=True)


class RoomSpecialty(ActiveRecord, Base):
    __tablename__ = "room_specialty"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["room.tenant_id", "room.id"],
            name="fk_room_specialty_room",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "specialty_id"],
            ["specialty.tenant_id", "specialty.id"],
            name="fk_room_specialty_specialty",
        ),
    )
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), primary_key=True)
    room_id: Mapped[UUID] = mapped_column(primary_key=True)
    specialty_id: Mapped[UUID] = mapped_column(primary_key=True)
