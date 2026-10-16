from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import Engine, text


@dataclass
class ClinicFactory:
    """Administrative identity seed data, independent of the future ORM."""

    admin_engine: Engine

    def tenant(self, name: str = "Organization") -> UUID:
        tenant_id = uuid4()
        with self.admin_engine.begin() as connection:
            connection.execute(
                text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
                {"id": tenant_id, "name": name},
            )
        return tenant_id

    def user(self, name: str = "Administrator") -> UUID:
        user_id = uuid4()
        with self.admin_engine.begin() as connection:
            connection.execute(
                text("INSERT INTO users (id, name) VALUES (:id, :name)"),
                {"id": user_id, "name": name},
            )
        return user_id

    def membership(self, tenant_id: UUID, user_id: UUID) -> None:
        with self.admin_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO user_tenants (tenant_id, user_id) "
                    "VALUES (:tenant, :user)"
                ),
                {"tenant": tenant_id, "user": user_id},
            )
