from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from factories import ClinicFactory
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import ProgrammingError

from clinic_api.environment import EnvironmentVariable

API_ROOT = Path(__file__).resolve().parents[1]


def test_migration_requires_its_own_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(EnvironmentVariable.MIGRATION_DATABASE_URL, raising=False)
    with pytest.raises(ValueError, match=EnvironmentVariable.MIGRATION_DATABASE_URL):
        command.upgrade(Config(str(API_ROOT / "alembic.ini")), "head")


def test_application_engine_uses_runtime_credentials() -> None:
    from clinic_api.db.session import create_engine
    from clinic_api.settings import Settings

    engine = create_engine(Settings().database_url)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT current_user")) == "clinic_runtime"
    finally:
        engine.dispose()


def test_upgrade_downgrade_upgrade(
    admin_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Migration tooling never falls back to, or requires, the runtime credential.
    monkeypatch.delenv(EnvironmentVariable.DATABASE_URL, raising=False)
    assert (API_ROOT / "alembic.ini").is_file(), "Alembic configuration is missing"
    config = Config(str(API_ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    assert {"tenant", "user", "user_tenant"} <= set(
        inspect(admin_engine).get_table_names()
    )
    command.downgrade(config, "base")
    assert set(inspect(admin_engine).get_table_names()) <= {"alembic_version"}
    command.upgrade(config, "head")
    assert {"tenant", "user", "user_tenant"} <= set(
        inspect(admin_engine).get_table_names()
    )


def test_runtime_role_is_not_privileged(runtime_engine: Engine) -> None:
    with runtime_engine.connect() as connection:
        role = connection.execute(
            text(
                "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
            )
        ).one()
    assert role.rolsuper is False
    assert role.rolbypassrls is False


def test_identity_tables_require_tenant_context(
    admin_engine: Engine, runtime_engine: Engine, factory: ClinicFactory
) -> None:
    tenant_id, user_id = factory.tenant(), factory.user()
    factory.membership(tenant_id, user_id)
    with admin_engine.begin() as connection:
        rls = connection.execute(
            text(
                "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE relname IN ('tenant', 'user', 'user_tenant')"
            )
        ).all()
        assert len(rls) == 3
        assert all(row.relrowsecurity and row.relforcerowsecurity for row in rls)
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM pg_policies WHERE schemaname = 'public' "
                    "AND tablename IN ('tenant', 'user', 'user_tenant')"
                )
            )
            == 3
        )
        assert (
            connection.scalar(
                text("SELECT count(*) FROM pg_extension WHERE extname = 'btree_gist'")
            )
            == 1
        )
    for table in ("tenant", '"user"', "user_tenant"):
        with runtime_engine.connect() as connection:
            assert connection.execute(text(f"SELECT * FROM {table}")).all() == []
        for statement in (f"DELETE FROM {table}", f"UPDATE {table} SET active = false"):
            with pytest.raises(ProgrammingError), runtime_engine.begin() as connection:
                connection.execute(text(statement))
    for statement, params in (
        ("INSERT INTO tenant (id, name) VALUES (:id, 'Denied')", {"id": uuid4()}),
        ("INSERT INTO \"user\" (id, name) VALUES (:id, 'Denied')", {"id": uuid4()}),
        (
            "INSERT INTO user_tenant (tenant_id, user_id) VALUES (:tenant, :user)",
            {"tenant": tenant_id, "user": user_id},
        ),
    ):
        with (
            pytest.raises(ProgrammingError),
            runtime_engine.begin() as connection,
        ):
            connection.execute(text(statement), params)
    with admin_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM tenant")) == 1
        assert connection.scalar(text('SELECT count(*) FROM "user"')) == 1
        assert connection.scalar(text("SELECT count(*) FROM user_tenant")) == 1
