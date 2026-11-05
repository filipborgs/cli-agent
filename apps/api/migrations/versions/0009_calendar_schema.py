"""Persist clinic_closure, person_block."""

import sqlalchemy as sa
from alembic import op

revision = "0009_calendar_schema"
down_revision = "0008_replacement_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinic_closure",
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
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_clinic_closure_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_clinic_closure_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_clinic_closure_clinic",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_clinic_closure_interval"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_clinic_closure_user_tenant",
        ),
    )
    op.execute("ALTER TABLE clinic_closure ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE clinic_closure FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON clinic_closure TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY clinic_closure_admin ON clinic_closure USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "person_block",
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
        sa.Column("patient_id", sa.Uuid(), nullable=True),
        sa.Column("therapist_id", sa.Uuid(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_person_block_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_person_block_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_person_block_patient",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_person_block_therapist",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_person_block_interval"),
        sa.CheckConstraint(
            "(patient_id IS NOT NULL) <> (therapist_id IS NOT NULL)",
            name="ck_person_block_one_person",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_person_block_user_tenant",
        ),
    )
    op.execute("ALTER TABLE person_block ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE person_block FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON person_block TO clinic_runtime")
    op.execute(
        "CREATE POLICY person_block_admin ON person_block USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.execute(
        "CREATE INDEX ix_clinic_closure_interval ON clinic_closure USING gist (tenant_id, tstzrange(starts_at, ends_at, '[)'))"
    )
    op.execute(
        "CREATE INDEX ix_person_block_interval ON person_block USING gist (tenant_id, tstzrange(starts_at, ends_at, '[)'))"
    )


def downgrade() -> None:
    op.drop_table("person_block")
    op.drop_table("clinic_closure")
