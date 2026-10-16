"""Founding identity tables, fail-closed RLS and scheduling extension."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_identity"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column[sa.DateTime]]:
    return [
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
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    for table in ("tenants", "users"):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *_timestamps(),
            sa.PrimaryKeyConstraint("id", name=f"pk_{table}"),
        )
    op.create_table(
        "user_tenants",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="admin"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("tenant_id", "user_id", name="pk_user_tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_user_tenants_tenant_id"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_tenants_user_id"
        ),
        sa.CheckConstraint("role = 'admin'", name="ck_user_tenants_admin_role"),
    )
    for table in ("tenants", "users", "user_tenants"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    # Migration bookkeeping is not application data, despite bootstrap defaults.
    op.execute("REVOKE ALL ON TABLE alembic_version FROM clinic_runtime")


def downgrade() -> None:
    op.drop_table("user_tenants")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
