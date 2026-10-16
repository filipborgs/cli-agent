from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from clinic_api.domain.identity.context import AccessContext


@dataclass
class ClinicFactory:
    """Administrative identity seed data, independent of the future ORM."""

    admin_engine: Engine

    def tenant(self, name: str = "Organization") -> UUID:
        tenant_id = uuid4()
        with self.admin_engine.begin() as connection:
            connection.execute(
                text("INSERT INTO tenant (id, name) VALUES (:id, :name)"),
                {"id": tenant_id, "name": name},
            )
        return tenant_id

    def user(self, name: str = "Administrator") -> UUID:
        user_id = uuid4()
        with self.admin_engine.begin() as connection:
            connection.execute(
                text('INSERT INTO "user" (id, name) VALUES (:id, :name)'),
                {"id": user_id, "name": name},
            )
        return user_id

    def membership(self, tenant_id: UUID, user_id: UUID) -> None:
        with self.admin_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO user_tenant (tenant_id, user_id) "
                    "VALUES (:tenant, :user)"
                ),
                {"tenant": tenant_id, "user": user_id},
            )

    def identity(self) -> AccessContext:
        tenant_id = self.tenant()
        user_id = self.user()
        self.membership(tenant_id, user_id)
        return AccessContext(user_id=user_id, tenant_id=tenant_id)

    def context_for(self, user_id: UUID, tenant_id: UUID) -> AccessContext:
        return AccessContext(user_id=user_id, tenant_id=tenant_id)

    def deactivate_membership(self, tenant_id: UUID, user_id: UUID) -> None:
        with self.admin_engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE user_tenant SET active = false WHERE tenant_id = :tenant_id AND user_id = :user_id"
                ),
                {"tenant_id": tenant_id, "user_id": user_id},
            )
