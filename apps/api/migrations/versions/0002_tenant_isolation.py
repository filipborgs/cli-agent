"""Authorize tenant identity access with transaction-local RLS context."""

from alembic import op

revision = "0002_tenant_isolation"
down_revision = "0001_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    op.execute(
        "REVOKE INSERT, UPDATE, DELETE ON tenants, users, user_tenants FROM clinic_runtime"
    )
    op.execute("GRANT SELECT ON tenants, users, user_tenants TO clinic_runtime")
    op.execute(
        "CREATE POLICY tenant_self ON tenants USING (id = NULLIF(current_setting('app.tenant_id', true), '')::uuid AND EXISTS (SELECT 1 FROM user_tenants WHERE tenant_id = tenants.id AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid AND active AND role = 'admin'))"
    )
    op.execute(
        "CREATE POLICY user_self ON users USING (id = NULLIF(current_setting('app.user_id', true), '')::uuid)"
    )
    op.execute(
        "CREATE POLICY membership_self ON user_tenants USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)"
    )


def downgrade() -> None:
    op.execute("DROP POLICY membership_self ON user_tenants")
    op.execute("DROP POLICY user_self ON users")
    op.execute("DROP POLICY tenant_self ON tenants")
    op.execute(
        "GRANT INSERT, UPDATE, DELETE ON tenants, users, user_tenants TO clinic_runtime"
    )
