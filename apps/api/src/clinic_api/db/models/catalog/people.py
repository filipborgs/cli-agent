from sqlalchemy import Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base
from clinic_api.db.models.common import CatalogEntity


class Patient(CatalogEntity, Base):
    __tablename__ = "patient"
    __table_args__ = (UniqueConstraint("tenant_id", "id", name="uq_patient_tenant_id"),)
    name: Mapped[str] = mapped_column(Text)


class Therapist(CatalogEntity, Base):
    __tablename__ = "therapist"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_therapist_tenant_id"),
    )
    name: Mapped[str] = mapped_column(Text)
