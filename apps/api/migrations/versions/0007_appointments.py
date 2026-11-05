"""Persist appointment, appointment_event."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_appointments"
down_revision = "0006_weekly_slots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointment",
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
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("therapist_id", sa.Uuid(), nullable=False),
        sa.Column("specialty_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'scheduled'")
        ),
        sa.Column("weekly_slot_id", sa.Uuid(), nullable=True),
        sa.Column("occurrence_date", sa.Date(), nullable=True),
        sa.Column(
            "manually_adjusted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "replacement_decision",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'not_applicable'"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_appointment_tenant"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_appointment_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id"],
            ["treatment_plan.tenant_id", "treatment_plan.id"],
            name="fk_appointment_treatment_plan",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id"],
            ["clinic.tenant_id", "clinic.id"],
            name="fk_appointment_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["room.tenant_id", "room.id"],
            name="fk_appointment_room",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patient_id"],
            ["patient.tenant_id", "patient.id"],
            name="fk_appointment_patient",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "therapist_id"],
            ["therapist.tenant_id", "therapist.id"],
            name="fk_appointment_therapist",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "specialty_id"],
            ["specialty.tenant_id", "specialty.id"],
            name="fk_appointment_specialty",
        ),
        sa.ForeignKeyConstraint(
            [
                "tenant_id",
                "treatment_plan_id",
                "patient_id",
                "therapist_id",
                "specialty_id",
            ],
            [
                "treatment_plan.tenant_id",
                "treatment_plan.id",
                "treatment_plan.patient_id",
                "treatment_plan.therapist_id",
                "treatment_plan.specialty_id",
            ],
            name="fk_appointment_plan_identity",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "clinic_id", "room_id"],
            ["room.tenant_id", "room.clinic_id", "room.id"],
            name="fk_appointment_room_clinic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "treatment_plan_id", "clinic_id"],
            [
                "treatment_plan_clinic.tenant_id",
                "treatment_plan_clinic.treatment_plan_id",
                "treatment_plan_clinic.clinic_id",
            ],
            name="fk_appointment_treatment_plan_clinic",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_appointment_interval"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_appointment_duration"),
        sa.CheckConstraint(
            "origin IN ('routine', 'replacement')", name="ck_appointment_origin"
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled', 'patient_absent', 'therapist_absent', 'dispensed')",
            name="ck_appointment_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "weekly_slot_id"],
            ["weekly_slot.tenant_id", "weekly_slot.id"],
            name="fk_appointment_weekly_slot",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "weekly_slot_id", "treatment_plan_id"],
            [
                "weekly_slot.tenant_id",
                "weekly_slot.id",
                "weekly_slot.treatment_plan_id",
            ],
            name="fk_appointment_slot_plan",
        ),
        sa.CheckConstraint(
            "replacement_decision IN ('not_applicable', 'awaiting_decision', 'granted', 'denied')",
            name="ck_appointment_replacement_decision",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "treatment_plan_id",
            name="uq_appointment_tenant_id_id_treatment_plan_id",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("patient_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status IN ('scheduled', 'completed')"),
            name="ex_appointment_patient",
            using="gist",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("therapist_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status IN ('scheduled', 'completed')"),
            name="ex_appointment_therapist",
            using="gist",
        ),
        postgresql.ExcludeConstraint(
            ("tenant_id", "="),
            ("room_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            where=sa.text("status IN ('scheduled', 'completed')"),
            name="ex_appointment_room",
            using="gist",
        ),
    )
    op.execute("ALTER TABLE appointment ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE appointment FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON appointment TO clinic_runtime")
    op.execute(
        "CREATE POLICY appointment_admin ON appointment USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_table(
        "appointment_event",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "before",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "after",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name="fk_appointment_event_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_appointment_event_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "appointment_id"],
            ["appointment.tenant_id", "appointment.id"],
            name="fk_appointment_event_appointment",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["user_tenant.tenant_id", "user_tenant.user_id"],
            name="fk_appointment_event_user_tenant",
        ),
    )
    op.execute("ALTER TABLE appointment_event ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE appointment_event FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON appointment_event TO clinic_runtime"
    )
    op.execute(
        "CREATE POLICY appointment_event_admin ON appointment_event USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
    )
    op.create_index(
        "uq_appointment_occurrence",
        "appointment",
        ["tenant_id", "weekly_slot_id", "occurrence_date"],
        unique=True,
        postgresql_where=sa.text("weekly_slot_id IS NOT NULL"),
    )

    op.execute("""CREATE FUNCTION validate_appointment_resources() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
    BEGIN
      IF NEW.status NOT IN ('scheduled', 'completed') THEN RETURN NEW; END IF;
      IF TG_OP = 'UPDATE' THEN
        IF OLD.status IN ('scheduled', 'completed') AND
          ROW(NEW.tenant_id, NEW.treatment_plan_id, NEW.clinic_id, NEW.room_id,
              NEW.patient_id, NEW.therapist_id, NEW.specialty_id, NEW.starts_at, NEW.ends_at)
          IS NOT DISTINCT FROM
          ROW(OLD.tenant_id, OLD.treatment_plan_id, OLD.clinic_id, OLD.room_id,
              OLD.patient_id, OLD.therapist_id, OLD.specialty_id, OLD.starts_at, OLD.ends_at)
        THEN RETURN NEW; END IF;
      END IF;
      PERFORM 1 FROM public.treatment_plan p
        JOIN public.treatment_plan_clinic pc ON pc.tenant_id=p.tenant_id AND pc.treatment_plan_id=p.id AND pc.clinic_id=NEW.clinic_id
        JOIN public.clinic c ON c.tenant_id=p.tenant_id AND c.id=pc.clinic_id
        JOIN public.patient pat ON pat.tenant_id=p.tenant_id AND pat.id=p.patient_id
        JOIN public.therapist th ON th.tenant_id=p.tenant_id AND th.id=p.therapist_id
        JOIN public.specialty sp ON sp.tenant_id=p.tenant_id AND sp.id=p.specialty_id
        JOIN public.patient_clinic pac ON pac.tenant_id=p.tenant_id AND pac.patient_id=p.patient_id AND pac.clinic_id=c.id
        JOIN public.therapist_clinic tc ON tc.tenant_id=p.tenant_id AND tc.therapist_id=p.therapist_id AND tc.clinic_id=c.id
        JOIN public.therapist_specialty ts ON ts.tenant_id=p.tenant_id AND ts.therapist_id=p.therapist_id AND ts.specialty_id=p.specialty_id
        JOIN public.room r ON r.tenant_id=p.tenant_id AND r.id=NEW.room_id AND r.clinic_id=c.id
        JOIN public.room_specialty rs ON rs.tenant_id=p.tenant_id AND rs.room_id=r.id AND rs.specialty_id=p.specialty_id
      WHERE p.tenant_id=NEW.tenant_id AND p.id=NEW.treatment_plan_id
        AND pc.active AND c.active AND pat.active AND th.active AND sp.active
        AND pac.active AND tc.active AND ts.active AND r.active AND rs.active
      FOR SHARE OF p, pc, c, pat, th, sp, pac, tc, ts, r, rs;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid appointment resource qualification' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$""")
    op.execute(
        "CREATE TRIGGER appointment_resources BEFORE INSERT OR UPDATE ON appointment FOR EACH ROW EXECUTE FUNCTION validate_appointment_resources()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER appointment_resources ON appointment")
    op.execute("DROP FUNCTION validate_appointment_resources()")
    op.drop_table("appointment_event")
    op.drop_table("appointment")
