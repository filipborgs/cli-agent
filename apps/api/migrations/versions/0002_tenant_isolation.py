"""Authorize tenant identity access with transaction-local RLS context."""

from alembic import op

revision = "0002_tenant_isolation"
down_revision = "0001_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    op.execute(
        'REVOKE INSERT, UPDATE, DELETE ON tenant, "user", user_tenant FROM clinic_runtime'
    )
    op.execute('GRANT SELECT ON tenant, "user", user_tenant TO clinic_runtime')
    op.execute(
        "CREATE POLICY tenant_self ON tenant USING (id = NULLIF(current_setting('app.tenant_id', true), '')::uuid AND EXISTS (SELECT 1 FROM user_tenant WHERE tenant_id = tenant.id AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid AND active AND role = 'admin'))"
    )
    op.execute(
        "CREATE POLICY user_self ON \"user\" USING (id = NULLIF(current_setting('app.user_id', true), '')::uuid)"
    )
    op.execute(
        "CREATE POLICY membership_self ON user_tenant USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)"
    )


def downgrade() -> None:
    op.execute("DROP POLICY membership_self ON user_tenant")
    op.execute('DROP POLICY user_self ON "user"')
    op.execute("DROP POLICY tenant_self ON tenant")
    op.execute(
        'GRANT INSERT, UPDATE, DELETE ON tenant, "user", user_tenant TO clinic_runtime'
    )
