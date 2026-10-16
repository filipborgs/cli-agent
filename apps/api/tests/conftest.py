from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from factories import ClinicFactory
from sqlalchemy import Engine, inspect, text

from clinic_api.db.session import create_engine
from clinic_api.environment import EnvironmentVariable


@pytest.fixture(scope="session")
def admin_engine() -> Iterator[Engine]:
    engine = create_engine(EnvironmentVariable.MIGRATION_DATABASE_URL.required())
    try:
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def runtime_engine() -> Iterator[Engine]:
    engine = create_engine(EnvironmentVariable.DATABASE_URL.required())
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(admin_engine: Engine) -> Iterator[None]:
    def truncate() -> None:
        tables = [
            table
            for table in inspect(admin_engine).get_table_names(schema="public")
            if table != "alembic_version"
        ]
        if tables:
            quote = admin_engine.dialect.identifier_preparer.quote
            names = ", ".join(f"public.{quote(table)}" for table in tables)
            with admin_engine.begin() as connection:
                connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))

    truncate()
    yield
    truncate()


@pytest.fixture
def factory(admin_engine: Engine) -> ClinicFactory:
    return ClinicFactory(admin_engine)
