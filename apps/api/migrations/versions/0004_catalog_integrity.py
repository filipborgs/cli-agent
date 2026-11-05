"""Complete tenant-safe catalog references and administrative RLS."""

import sqlalchemy as sa
from alembic import op

revision = "0004_catalog_integrity"
down_revision = "0003_catalog"
branch_labels = None
depends_on = None

ENTITIES = ("clinic", "patient", "therapist", "specialty", "room")
ASSOCIATIONS = (
    ("patient_clinic", "patient", "clinic"),
    ("therapist_clinic", "therapist", "clinic"),
    ("therapist_specialty", "therapist", "specialty"),
    ("room_specialty", "room", "specialty"),
)


def timestamps():
    return [
        sa.Column(
            name,
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        )
        for name in ("created_at", "updated_at")
    ]


def upgrade() -> None:
    op.execute("DROP POLICY tenant_self ON tenant")
    op.execute("""CREATE POLICY tenant_self ON tenant USING (
        active AND id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        AND EXISTS (SELECT 1 FROM user_tenant m JOIN "user" u ON u.id = m.user_id
        WHERE m.tenant_id = tenant.id AND m.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
        AND m.active AND m.role = 'admin' AND u.active))""")
    op.execute("""CREATE FUNCTION clinic_has_admin_access(target uuid) RETURNS boolean
        LANGUAGE sql STABLE SECURITY INVOKER SET search_path = pg_catalog, public AS $$
        SELECT target = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        AND EXISTS (SELECT 1 FROM public.tenant t WHERE t.id = target)
        $$""")
    op.execute("REVOKE ALL ON FUNCTION clinic_has_admin_access(uuid) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION clinic_has_admin_access(uuid) TO clinic_runtime"
    )
    for table in ENTITIES:
        op.create_unique_constraint(f"uq_{table}_tenant_id", table, ["tenant_id", "id"])
        for column in timestamps():
            op.add_column(table, column)
    op.create_unique_constraint(
        "uq_room_clinic_id", "room", ["tenant_id", "clinic_id", "id"]
    )
    op.execute(
        "ALTER TABLE room RENAME CONSTRAINT room_tenant_id_clinic_id_normalized_name_key TO uq_room_name"
    )
    op.execute(
        "ALTER TABLE specialty RENAME CONSTRAINT specialty_tenant_id_normalized_name_key TO uq_specialty_name"
    )
    op.execute(
        "ALTER TABLE clinic RENAME CONSTRAINT clinic_default_duration_minutes_check TO ck_clinic_duration"
    )
    for table, col, target in (
        ("room", "clinic_id", "clinic"),
        ("patient_clinic", "patient_id", "patient"),
        ("patient_clinic", "clinic_id", "clinic"),
    ):
        op.drop_constraint(f"{table}_{col}_fkey", table, type_="foreignkey")
        op.create_foreign_key(
            f"fk_{table}_{target}",
            table,
            target,
            ["tenant_id", col],
            ["tenant_id", "id"],
        )
    op.create_foreign_key(
        "fk_patient_clinic_tenant", "patient_clinic", "tenant", ["tenant_id"], ["id"]
    )
    for column in timestamps():
        op.add_column("patient_clinic", column)
    for table, first, second in ASSOCIATIONS[1:]:
        op.create_table(
            table,
            sa.Column(
                "tenant_id", sa.Uuid(), sa.ForeignKey("tenant.id"), primary_key=True
            ),
            sa.Column(f"{first}_id", sa.Uuid(), primary_key=True),
            sa.Column(f"{second}_id", sa.Uuid(), primary_key=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *timestamps(),
            sa.ForeignKeyConstraint(
                ["tenant_id", f"{first}_id"],
                [f"{first}.tenant_id", f"{first}.id"],
                name=f"fk_{table}_{first}",
            ),
            sa.ForeignKeyConstraint(
                ["tenant_id", f"{second}_id"],
                [f"{second}.tenant_id", f"{second}.id"],
                name=f"fk_{table}_{second}",
            ),
        )
    op.execute("DROP POLICY clinic_tenant ON clinic")
    for table in (*ENTITIES, *(item[0] for item in ASSOCIATIONS)):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO clinic_runtime")
        op.execute(
            f"CREATE POLICY {table}_admin ON {table} USING (clinic_has_admin_access(tenant_id)) WITH CHECK (clinic_has_admin_access(tenant_id))"
        )


def downgrade() -> None:
    for table in (*ENTITIES, *(item[0] for item in ASSOCIATIONS)):
        op.execute(f"DROP POLICY {table}_admin ON {table}")
    for table, _, _ in reversed(ASSOCIATIONS[1:]):
        op.drop_table(table)
    op.drop_constraint("fk_patient_clinic_tenant", "patient_clinic", type_="foreignkey")
    for table, col, target in (
        ("room", "clinic_id", "clinic"),
        ("patient_clinic", "patient_id", "patient"),
        ("patient_clinic", "clinic_id", "clinic"),
    ):
        op.drop_constraint(f"fk_{table}_{target}", table, type_="foreignkey")
        op.create_foreign_key(f"{table}_{col}_fkey", table, target, [col], ["id"])
    op.drop_constraint("uq_room_clinic_id", "room", type_="unique")
    for table in (*ENTITIES, "patient_clinic"):
        for name in ("updated_at", "created_at"):
            op.drop_column(table, name)
    for table in ENTITIES:
        op.drop_constraint(f"uq_{table}_tenant_id", table, type_="unique")
    for table in (*ENTITIES[1:], "patient_clinic"):
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY clinic_tenant ON clinic USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
    )
    op.execute(
        "ALTER TABLE room RENAME CONSTRAINT uq_room_name TO room_tenant_id_clinic_id_normalized_name_key"
    )
    op.execute(
        "ALTER TABLE specialty RENAME CONSTRAINT uq_specialty_name TO specialty_tenant_id_normalized_name_key"
    )
    op.execute(
        "ALTER TABLE clinic RENAME CONSTRAINT ck_clinic_duration TO clinic_default_duration_minutes_check"
    )
    op.execute("DROP FUNCTION clinic_has_admin_access(uuid)")
    op.execute("DROP POLICY tenant_self ON tenant")
    op.execute(
        "CREATE POLICY tenant_self ON tenant USING (id = NULLIF(current_setting('app.tenant_id', true), '')::uuid AND EXISTS (SELECT 1 FROM user_tenant WHERE tenant_id = tenant.id AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid AND active AND role = 'admin'))"
    )
