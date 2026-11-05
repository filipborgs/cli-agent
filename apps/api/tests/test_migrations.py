import re
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, UniqueConstraint, inspect, text
from sqlalchemy.exc import DBAPIError


def default_sql(value):
    if value is None:
        return None
    return re.sub(r"::[a-z_ ]+", "", str(value)).strip("()")


def test_orm_matches_migrated_columns_keys_and_defaults(admin_engine):
    from clinic_api.db.base import Base
    from clinic_api.db.models.registry import register_models

    register_models()
    inspector = inspect(admin_engine)
    for table in Base.metadata.tables.values():
        reflected = {
            column["name"]: column for column in inspector.get_columns(table.name)
        }
        assert set(reflected) == set(table.columns.keys()), table.name
        for column in table.columns:
            actual = reflected[column.name]
            assert column.type.compile(dialect=admin_engine.dialect) == actual[
                "type"
            ].compile(dialect=admin_engine.dialect), (table.name, column.name, "type")
            assert column.nullable == actual["nullable"], (
                table.name,
                column.name,
                "nullable",
            )
            if column.computed is not None:
                assert default_sql(column.computed.sqltext) == default_sql(
                    actual["computed"]["sqltext"]
                )
                assert column.computed.persisted == actual["computed"]["persisted"]
            else:
                assert default_sql(
                    column.server_default.arg if column.server_default else None
                ) == default_sql(actual["default"]), (
                    table.name,
                    column.name,
                    "default",
                )
        assert set(inspector.get_pk_constraint(table.name)["constrained_columns"]) == {
            c.name for c in table.primary_key
        }
        expected_fk = {
            (
                tuple(fk.column_keys),
                tuple(element.target_fullname for element in fk.elements),
            )
            for fk in table.foreign_key_constraints
        }
        actual_fk = {
            (
                tuple(fk["constrained_columns"]),
                tuple(
                    f"{fk['referred_table']}.{name}" for name in fk["referred_columns"]
                ),
            )
            for fk in inspector.get_foreign_keys(table.name)
        }
        assert expected_fk == actual_fk, (table.name, "foreign keys")
        expected_unique = {
            tuple(c.name for c in constraint.columns)
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert expected_unique == {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints(table.name)
        }, (table.name, "unique")
        expected_checks = {
            constraint.name
            for constraint in table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        assert expected_checks == {
            item["name"] for item in inspector.get_check_constraints(table.name)
        }, (table.name, "checks")


def test_all_migrations_roundtrip_and_security_objects(admin_engine):
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.downgrade(config, "base")
    assert set(inspect(admin_engine).get_table_names()) <= {"alembic_version"}
    command.upgrade(config, "head")
    from clinic_api.db.base import Base

    assert set(inspect(admin_engine).get_table_names()) == set(Base.metadata.tables) | {
        "alembic_version"
    }
    with admin_engine.connect() as connection:
        rls = connection.execute(
            text(
                "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r' AND relname <> 'alembic_version'"
            )
        ).all()
        assert len(rls) == 26
        assert all(row.relrowsecurity and row.relforcerowsecurity for row in rls)
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM pg_constraint WHERE contype='x' AND connamespace='public'::regnamespace"
                )
            )
            == 4
        )
        indexes = set(
            connection.scalars(
                text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
            )
        )
        assert {
            "uq_appointment_occurrence",
            "uq_appointment_due_scheduled",
            "uq_appointment_due_completed",
            "ix_clinic_closure_interval",
            "ix_person_block_interval",
        } <= indexes
        triggers = set(
            connection.scalars(
                text(
                    "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN ('appointment'::regclass, 'replacement_due'::regclass)"
                )
            )
        )
        assert triggers == {
            "appointment_resources",
            "replacement_origin",
            "preserve_replacement_origin",
        }


@pytest.mark.parametrize(
    "statement",
    [
        "CREATE TABLE unauthorized (id integer)",
        "ALTER TABLE patient ADD COLUMN denied text",
        "SET ROLE clinic_migrator",
    ],
)
def test_runtime_cannot_migrate_or_assume_migrator(runtime_engine, statement):
    with pytest.raises(DBAPIError), runtime_engine.begin() as connection:
        connection.execute(text(statement))


def test_orm_matches_postgresql_check_exclusion_and_index_definitions(admin_engine):
    """Let PostgreSQL normalize both artifacts; compare expressions, not names."""
    from sqlalchemy import Column, MetaData, Table
    from sqlalchemy.dialects.postgresql import ExcludeConstraint
    from sqlalchemy.schema import AddConstraint, CreateIndex, CreateTable, DropTable

    from clinic_api.db.base import Base

    with admin_engine.begin() as connection:
        for table in Base.metadata.tables.values():
            constraints = [
                item
                for item in table.constraints
                if isinstance(item, (CheckConstraint, ExcludeConstraint))
            ]
            if not constraints and not table.indexes:
                continue
            probe = Table(
                "orm_constraint_probe",
                MetaData(),
                *(Column(column.name, column.type) for column in table.columns),
                prefixes=["TEMPORARY"],
            )
            connection.execute(CreateTable(probe))
            table_sql = admin_engine.dialect.identifier_preparer.format_table(table)
            for constraint in constraints:
                ddl = str(
                    AddConstraint(constraint).compile(dialect=admin_engine.dialect)
                )
                connection.exec_driver_sql(
                    ddl.replace(
                        f"ALTER TABLE {table_sql} ",
                        "ALTER TABLE pg_temp.orm_constraint_probe ",
                        1,
                    )
                )
                sql = text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=to_regclass(:table) AND conname=:name"
                )
                expected = connection.scalar(
                    sql,
                    {"table": "pg_temp.orm_constraint_probe", "name": constraint.name},
                )
                actual = connection.scalar(
                    sql, {"table": f"public.{table_sql}", "name": constraint.name}
                )
                assert expected == actual, (table.name, constraint.name, "definition")
            for index in table.indexes:
                ddl = str(CreateIndex(index).compile(dialect=admin_engine.dialect))
                connection.exec_driver_sql(
                    ddl.replace(
                        f" ON {table_sql} ", " ON pg_temp.orm_constraint_probe ", 1
                    )
                )
                # Temp schemas may be printed explicitly, so identify by pg_class.relname.
                sql = text(
                    "SELECT pg_get_indexdef(i.indexrelid) FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indrelid=to_regclass(:table) AND c.relname=:name"
                )
                expected = connection.scalar(
                    sql, {"table": "pg_temp.orm_constraint_probe", "name": index.name}
                )
                actual = connection.scalar(
                    sql, {"table": f"public.{table_sql}", "name": index.name}
                )
                assert (
                    expected.split(" USING ", 1)[1] == actual.split(" USING ", 1)[1]
                ), (table.name, index.name, "definition")
            connection.execute(DropTable(probe))
