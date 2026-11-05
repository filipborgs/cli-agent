"""Persist treatment_plan, treatment_plan_clinic, patient_availability, therapist_availability, clinic_hours."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_treatment_planning"
down_revision = "0004_catalog_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "treatment_plan",
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
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("therapist_id", sa.Uuid(), nullable=False),
        sa.Column("specialty_id", sa.Uuid(), nullable=False),
        sa.Column("sessions_per_week", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_treatment_plan_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_treatment_plan_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_treatment_plan_patient",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_treatment_plan_therapist",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "specialty_id"],
            ["specialty.tenant_id", "specialty.id"],
            name="fk_treatment_plan_specialty",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_treatment_plan_validity",
        ),
        sa.CheckConstraint("sessions_per_week > 0", name="ck_treatment_plan_frequency"),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_treatment_plan_duration",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "patient_id",
            "therapist_id",
            "specialty_id",
            name="uq_treatment_plan_identity",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("patient_id", "="),
            ("therapist_id", "="),
            ("specialty_id", "="),
            (sa.text("daterange(valid_from, valid_until + 1, '[)')"), "&&"),
            name="ex_treatment_plan_validity",
            using="gist",
        ),
    )
    op.execute("ALTER TABLE treatment_plan ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE treatment_plan FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON treatment_plan TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY treatment_plan_admin ON treatment_plan USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "treatment_plan_clinic",
        sa.Column("tenant_id", sa.Uuid(), primary_key=True),
        sa.Column("treatment_plan_id", sa.Uuid(), primary_key=True),
        sa.Column("clinic_id", sa.Uuid(), primary_key=True),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_treatment_plan_clinic_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_treatment_plan_clinic_clinic",
        ),
    )
    op.execute("ALTER TABLE treatment_plan_clinic ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE treatment_plan_clinic FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON treatment_plan_clinic TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY treatment_plan_clinic_admin ON treatment_plan_clinic USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "patient_availability",
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
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
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
    op.execute("ALTER TABLE patient_availability ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE patient_availability FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON patient_availability TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY patient_availability_admin ON patient_availability USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "therapist_availability",
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
        sa.Column("therapist_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
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
    op.execute("ALTER TABLE therapist_availability ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE therapist_availability FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON therapist_availability TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY therapist_availability_admin ON therapist_availability USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "clinic_hours",
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
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
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
    op.execute("ALTER TABLE clinic_hours ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE clinic_hours FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON clinic_hours TO clinic_runtime")
    op.execute(
        "CREATE POLICY clinic_hours_admin ON clinic_hours USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )


def downgrade() -> None:
    op.drop_table("clinic_hours")
    op.drop_table("therapist_availability")
    op.drop_table("patient_availability")
    op.drop_table("treatment_plan_clinic")
    op.drop_table("treatment_plan")
