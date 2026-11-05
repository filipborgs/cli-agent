from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base
from clinic_api.db.models.common import CatalogEntity


class Clinic(CatalogEntity, Base):
    __tablename__ = "clinic"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_clinic_tenant_id"),
        CheckConstraint("default_duration_minutes > 0", name="ck_clinic_duration"),
    )
    name: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text)
    default_duration_minutes: Mapped[int] = mapped_column(Integer)


class Room(CatalogEntity, Base):
    __tablename__ = "room"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_room_tenant_id"),
        UniqueConstraint("tenant_id", "clinic_id", "id", name="uq_room_clinic_id"),
        UniqueConstraint(
            "tenant_id", "clinic_id", "normalized_name", name="uq_room_name"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_room_clinic",
        ),
    )
    clinic_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
