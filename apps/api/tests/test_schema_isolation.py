from uuid import uuid4

import pytest
from schema_support import context, full_schema
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

BUSINESS_TABLES = (
    "clinic",
    "patient",
    "therapist",
    "specialty",
    "room",
    "patient_clinic",
    "therapist_clinic",
    "therapist_specialty",
    "room_specialty",
    "treatment_plan",
    "treatment_plan_clinic",
    "patient_availability",
    "therapist_availability",
    "clinic_hours",
    "weekly_slot",
    "appointment",
    "appointment_event",
    "replacement_due",
    "clinic_closure",
    "person_block",
    "monthly_agenda",
    "generation_run",
    "generation_deficit",
)


@pytest.mark.parametrize("table", BUSINESS_TABLES)
def test_business_table_dml_isolation_and_roundtrip(
    factory, admin_engine, runtime_engine, table
):
    first, other = factory.identity(), factory.identity()
    with admin_engine.begin() as connection:
        rows = full_schema(connection, first)
        full_schema(connection, other)
    with runtime_engine.begin() as connection:
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
        context(connection, first.tenant_id, first.user_id)
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 1
        assert connection.execute(
            text(f"UPDATE {table} SET tenant_id=tenant_id RETURNING tenant_id")
        ).scalars().all() == [first.tenant_id]
        # Try to move an authorized row into another tenant: WITH CHECK must reject.
        with pytest.raises(DBAPIError) as caught, connection.begin_nested():
            connection.execute(
                text(f"UPDATE {table} SET tenant_id=:other"), {"other": other.tenant_id}
            )
        assert caught.value.orig.sqlstate == "42501"
        context(connection, other.tenant_id, first.user_id)
        assert (
            connection.execute(
                text(f"UPDATE {table} SET tenant_id=tenant_id RETURNING tenant_id")
            ).all()
            == []
        )
        assert (
            connection.execute(text(f"DELETE FROM {table} RETURNING tenant_id")).all()
            == []
        )
        from clinic_api.db.base import Base

        writable = {
            key: value
            for key, value in rows[table].items()
            if Base.metadata.tables[table].c[key].computed is None
        }
        columns = ", ".join(writable)
        placeholders = ", ".join(":" + name for name in writable)
        # Clone a row via bound values; JSONB values use JSON strings for SQL parameters.
        import json

        values = {
            key: json.dumps(value) if isinstance(value, dict) else value
            for key, value in writable.items()
        }
        if "id" in values:
            values["id"] = uuid4()
        with pytest.raises(DBAPIError) as caught, connection.begin_nested():
            connection.execute(
                text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), values
            )
        assert caught.value.orig.sqlstate == "42501"
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from clinic_api.db.base import Base

    model = next(
        mapper.class_
        for mapper in Base.registry.mappers
        if mapper.local_table.name == table
    )
    with Session(admin_engine) as session:
        entity = session.scalars(
            select(model).where(model.tenant_id == first.tenant_id)
        ).one()
        assert entity.tenant_id == first.tenant_id


@pytest.mark.parametrize("inactive", ["tenant", "user", "user_tenant"])
def test_inactive_identity_denies_every_business_table(
    factory, admin_engine, runtime_engine, inactive
):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        full_schema(connection, identity)
        connection.execute(text(f'UPDATE "{inactive}" SET active=false'))
    with runtime_engine.begin() as connection:
        context(connection, identity.tenant_id, identity.user_id)
        for table in BUSINESS_TABLES:
            assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0, table


@pytest.mark.parametrize("table", BUSINESS_TABLES)
def test_business_foreign_keys_reject_cross_tenant_references(
    factory, admin_engine, table
):
    from sqlalchemy import inspect

    first, other = factory.identity(), factory.identity()
    with admin_engine.begin() as connection:
        full_schema(connection, first)
        foreign_rows = full_schema(connection, other)
    for fk in inspect(admin_engine).get_foreign_keys(table):
        if fk["referred_table"] in ("tenant", "user_tenant"):
            continue
        changes = {
            local: foreign_rows[fk["referred_table"]][remote]
            for local, remote in zip(
                fk["constrained_columns"], fk["referred_columns"], strict=True
            )
            if local != "tenant_id" and local != "original_origin"
        }
        assignment = ", ".join(f"{name} = :{name}" for name in changes)
        with pytest.raises(DBAPIError) as caught, admin_engine.begin() as connection:
            connection.execute(
                text(f"UPDATE {table} SET {assignment} WHERE tenant_id=:own"),
                {**changes, "own": first.tenant_id},
            )
        assert caught.value.orig.sqlstate in ("23503", "23514"), (table, fk)
