"""Persist weekly_slot."""

import sqlalchemy as sa
from alembic import op

revision = "0006_weekly_slots"
down_revision = "0005_treatment_planning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_slot",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("treatment_plan_id", sa.Uuid(), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
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
    op.execute("ALTER TABLE weekly_slot ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE weekly_slot FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON weekly_slot TO clinic_runtime")
    op.execute(
        "CREATE POLICY weekly_slot_admin ON weekly_slot USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )


def downgrade() -> None:
    op.drop_table("weekly_slot")
