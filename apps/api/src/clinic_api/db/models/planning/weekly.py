from datetime import date, datetime, time
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from clinic_api.db.base import Base


class WeeklySlot(Base):
    __tablename__ = "weekly_slot"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_weekly_slot_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_weekly_slot_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_weekly_slot_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_weekly_slot_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["room.tenant_id", "room.id"],
            name="fk_weekly_slot_room",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id", "room_id"],
            ["room.tenant_id", "room.clinic_id", "room.id"],
            name="fk_weekly_slot_room_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id", "clinic_id"],
            [
                "treatment_plan_clinic.tenant_id",
                "treatment_plan_clinic.treatment_plan_id",
                "treatment_plan_clinic.clinic_id",
            ],
            name="fk_weekly_slot_treatment_plan_clinic",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_weekly_slot_validity",
        ),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_weekly_slot_weekday"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_weekly_slot_duration"),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "treatment_plan_id",
            name="uq_weekly_slot_tenant_id_id_treatment_plan_id",
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
    weekday: Mapped[int] = mapped_column(sa.SmallInteger(), nullable=False)
    start_time: Mapped[time] = mapped_column(sa.Time(), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    valid_from: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(sa.Date(), nullable=True)
