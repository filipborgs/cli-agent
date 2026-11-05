"""Persist monthly_agenda, generation_run, generation_deficit."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_monthly_agenda_schema"
down_revision = "0009_calendar_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monthly_agenda",
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
        sa.Column("clinic_id", sa.Uuid(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_monthly_agenda_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_monthly_agenda_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_monthly_agenda_clinic",
        ),
        sa.CheckConstraint(
            "EXTRACT(DAY FROM month) = 1", name="ck_monthly_agenda_month"
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "clinic_id",
            "month",
            name="uq_monthly_agenda_tenant_id_clinic_id_month",
        ),
    )
    op.execute("ALTER TABLE monthly_agenda ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE monthly_agenda FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON monthly_agenda TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY monthly_agenda_admin ON monthly_agenda USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "generation_run",
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
        sa.Column("monthly_agenda_id", sa.Uuid(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'running'")
        ),
        sa.Column(
            "parameters",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_generation_run_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_generation_run_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "monthly_agenda_id"],
            ["monthly_agenda.tenant_id", "monthly_agenda.id"],
            name="fk_generation_run_monthly_agenda",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'partial', 'failed')",
            name="ck_generation_run_status",
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_generation_run_times",
        ),
    )
    op.execute("ALTER TABLE generation_run ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE generation_run FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON generation_run TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY generation_run_admin ON generation_run USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "generation_deficit",
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
        sa.Column("generation_run_id", sa.Uuid(), nullable=False),
        sa.Column("treatment_plan_id", sa.Uuid(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("missing_count", sa.Integer(), nullable=False),
        sa.Column("reason_code", sa.Text(), nullable=False),
        sa.Column(
            "details",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_generation_deficit_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_generation_deficit_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "generation_run_id"],
            ["generation_run.tenant_id", "generation_run.id"],
            name="fk_generation_deficit_generation_run",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_generation_deficit_treatment_plan",
        ),
        sa.CheckConstraint("missing_count > 0", name="ck_generation_deficit_missing"),
        sa.CheckConstraint(
            "EXTRACT(ISODOW FROM week_start) = 1", name="ck_generation_deficit_week"
        ),
        sa.CheckConstraint(
            "reason_code IN ('no_common_availability', 'no_compatible_room', 'resource_conflict')",
            name="ck_generation_deficit_reason_code",
        ),
    )
    op.execute("ALTER TABLE generation_deficit ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE generation_deficit FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON generation_deficit TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY generation_deficit_admin ON generation_deficit USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )


def downgrade() -> None:
    op.drop_table("generation_deficit")
    op.drop_table("generation_run")
    op.drop_table("monthly_agenda")
