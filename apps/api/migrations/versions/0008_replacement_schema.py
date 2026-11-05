"""Persist replacement_due."""

import sqlalchemy as sa
from alembic import op

revision = "0008_replacement_schema"
down_revision = "0007_appointments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_appointment_origin_identity",
        "appointment",
        ["tenant_id", "id", "treatment_plan_id", "origin"],
    )
    op.create_table(
        "replacement_due",
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
        sa.Column("original_appointment_id", sa.Uuid(), nullable=False),
        sa.Column(
            "original_origin",
            sa.Text(),
            sa.Computed("'routine'", persisted=True),
            nullable=False,
        ),
        sa.Column("treatment_plan_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'pending'")
        ),
        sa.Column("decided_by", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_replacement_due_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_replacement_due_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "original_appointment_id"],
            ["appointment.tenant_id", "appointment.id"],
            name="fk_replacement_due_appointment",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_replacement_due_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            [
                "tenant_id",
                "original_appointment_id",
                "treatment_plan_id",
                "original_origin",
            ],
            [
                "appointment.tenant_id",
                "appointment.id",
                "appointment.treatment_plan_id",
                "appointment.origin",
            ],
            name="fk_replacement_due_original_plan",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "original_appointment_id",
            name="uq_replacement_due_tenant_id_original_appointment_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "treatment_plan_id",
            name="uq_replacement_due_tenant_id_id_treatment_plan_id",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'scheduled', 'completed', 'closed')",
            name="ck_replacement_due_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "decided_by"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_replacement_due_user_tenant",
        ),
        sa.CheckConstraint(
            "(decided_by IS NULL) = (decided_at IS NULL)",
            name="ck_replacement_due_decision",
        ),
        sa.CheckConstraint(
            "status <> 'closed' OR (closed_reason IS NOT NULL AND length(trim(closed_reason)) > 0 AND decided_by IS NOT NULL)",
            name="ck_replacement_due_closure",
        ),
    )
    op.execute("ALTER TABLE replacement_due ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE replacement_due FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON replacement_due TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY replacement_due_admin ON replacement_due USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )

    op.add_column(
        "appointment", sa.Column("replacement_due_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_appointment_replacement",
        "appointment",
        "replacement_due",
        ["tenant_id", "replacement_due_id", "treatment_plan_id"],
        ["tenant_id", "id", "treatment_plan_id"],
    )
    op.create_check_constraint(
        "ck_appointment_origin_fields",
        "appointment",
        "(origin = 'routine' AND weekly_slot_id IS NOT NULL AND occurrence_date IS NOT NULL AND replacement_due_id IS NULL) OR (origin = 'replacement' AND weekly_slot_id IS NULL AND occurrence_date IS NULL AND replacement_due_id IS NOT NULL)",
    )
    for status in ("scheduled", "completed"):
        op.create_index(
            f"uq_appointment_due_{status}",
            "appointment",
            ["tenant_id", "replacement_due_id"],
            unique=True,
            postgresql_where=sa.text(f"origin = 'replacement' AND status = '{status}'"),
        )
    op.execute("""CREATE FUNCTION validate_replacement_origin() RETURNS trigger
      LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
      BEGIN
        IF current_user = 'clinic_runtime' AND NOT public.clinic_has_admin_access(NEW.tenant_id) THEN
          RAISE EXCEPTION 'Administrative context required' USING ERRCODE='42501';
        END IF;
        PERFORM 1 FROM public.appointment
        WHERE tenant_id=NEW.tenant_id AND id=NEW.original_appointment_id
          AND treatment_plan_id=NEW.treatment_plan_id AND origin='routine'
        FOR SHARE;
        IF NOT FOUND THEN
          RAISE EXCEPTION 'Replacement origin must be routine' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
      END $$""")
    op.execute(
        "CREATE TRIGGER replacement_origin BEFORE INSERT OR UPDATE ON replacement_due FOR EACH ROW EXECUTE FUNCTION validate_replacement_origin()"
    )
    op.execute("""CREATE FUNCTION preserve_replacement_origin() RETURNS trigger
      LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
      BEGIN
        IF NEW.origin <> 'routine' AND EXISTS (
          SELECT 1 FROM public.replacement_due WHERE tenant_id=OLD.tenant_id AND original_appointment_id=OLD.id
        ) THEN RAISE EXCEPTION 'Referenced routine origin is immutable' USING ERRCODE='23514'; END IF;
        RETURN NEW;
      END $$""")
    op.execute(
        "CREATE TRIGGER preserve_replacement_origin BEFORE UPDATE OF origin ON appointment FOR EACH ROW EXECUTE FUNCTION preserve_replacement_origin()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER preserve_replacement_origin ON appointment")
    op.execute("DROP FUNCTION preserve_replacement_origin()")
    op.execute("DROP TRIGGER replacement_origin ON replacement_due")
    op.execute("DROP FUNCTION validate_replacement_origin()")
    for status in ("scheduled", "completed"):
        op.drop_index(f"uq_appointment_due_{status}", table_name="appointment")
    op.drop_constraint("ck_appointment_origin_fields", "appointment", type_="check")
    op.drop_constraint("fk_appointment_replacement", "appointment", type_="foreignkey")
    op.drop_column("appointment", "replacement_due_id")
    op.drop_table("replacement_due")
    op.drop_constraint("uq_appointment_origin_identity", "appointment", type_="unique")
