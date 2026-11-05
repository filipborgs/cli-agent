from uuid import uuid4

import pytest
from schema_support import catalog, context, insert
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

TABLES = (
    "clinic",
    "patient",
    "therapist",
    "specialty",
    "room",
    "patient_clinic",
    "therapist_clinic",
    "therapist_specialty",
    "room_specialty",
)


def test_catalog_associations_and_history(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = catalog(connection, identity.tenant_id)
        second = insert(
            connection,
            "clinic",
            tenant_id=identity.tenant_id,
            name="Segunda",
            timezone="UTC",
            default_duration_minutes=45,
        )
        connection.execute(
            text(
                "INSERT INTO patient_clinic (tenant_id, patient_id, clinic_id) VALUES (:tenant_id, :patient_id, :clinic)"
            ),
            {**ids, "clinic": second},
        )
        extra = insert(
            connection,
            "specialty",
            tenant_id=identity.tenant_id,
            name="Psico",
            normalized_name="psico",
        )
        for table, key in (
            ("therapist_specialty", "therapist_id"),
            ("room_specialty", "room_id"),
        ):
            connection.execute(
                text(
                    f"INSERT INTO {table} (tenant_id, {key}, specialty_id) VALUES (:tenant_id, :resource, :specialty)"
                ),
                {
                    "tenant_id": identity.tenant_id,
                    "resource": ids[key],
                    "specialty": extra,
                },
            )
            assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 2
        connection.execute(
            text("UPDATE patient SET active = false WHERE id = :patient_id"), ids
        )
        assert connection.scalar(text("SELECT count(*) FROM patient_clinic")) == 2


@pytest.mark.parametrize("table", TABLES)
def test_catalog_rls_requires_active_admin(
    factory, admin_engine, runtime_engine, table
):
    identity, other = factory.identity(), factory.identity()
    with admin_engine.begin() as connection:
        catalog(connection, identity.tenant_id)
        catalog(connection, other.tenant_id)
    with runtime_engine.begin() as connection:
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
        context(connection, identity.tenant_id, identity.user_id)
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 1
        assert connection.execute(
            text(f"UPDATE {table} SET active = active RETURNING tenant_id")
        ).scalars().all() == [identity.tenant_id]
        context(connection, other.tenant_id, identity.user_id)
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
        assert (
            connection.execute(text(f"DELETE FROM {table} RETURNING tenant_id")).all()
            == []
        )
    factory.deactivate_membership(identity.tenant_id, identity.user_id)
    with runtime_engine.begin() as connection:
        context(connection, identity.tenant_id, identity.user_id)
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0


@pytest.mark.parametrize(
    "table,column",
    [
        ("patient_clinic", "patient_id"),
        ("patient_clinic", "clinic_id"),
        ("therapist_clinic", "therapist_id"),
        ("therapist_specialty", "specialty_id"),
        ("room_specialty", "room_id"),
        ("room", "clinic_id"),
    ],
)
def test_catalog_foreign_tenant_reference_is_rejected(
    factory, admin_engine, table, column
):
    first, second = factory.identity(), factory.identity()
    with admin_engine.begin() as connection:
        own = catalog(connection, first.tenant_id)
        foreign = catalog(connection, second.tenant_id)
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        # Moving a reference across tenants must fail even with BYPASSRLS.
        connection.execute(
            text(f"UPDATE {table} SET {column} = :foreign WHERE tenant_id = :tenant"),
            {"foreign": foreign[column], "tenant": own["tenant_id"]},
        )


def test_catalog_orm_defaults_and_duration_check(factory, admin_engine):
    from clinic_api.db.models.catalog.facilities import Clinic

    identity = factory.identity()
    with Session(admin_engine) as session, session.begin():
        clinic = Clinic(
            id=uuid4(),
            tenant_id=identity.tenant_id,
            name="ORM",
            timezone="UTC",
            default_duration_minutes=30,
        )
        session.add(clinic)
        session.flush()
        session.refresh(clinic)
        assert clinic.active is True
        assert clinic.created_at is not None
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(
            connection,
            "clinic",
            tenant_id=identity.tenant_id,
            name="Invalid",
            timezone="UTC",
            default_duration_minutes=0,
        )


@pytest.mark.parametrize("table", ["specialty", "room"])
def test_normalized_name_unique_in_owner_scope(factory, admin_engine, table):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = catalog(connection, identity.tenant_id)
    values = {
        "tenant_id": identity.tenant_id,
        "name": "Duplicate",
        "normalized_name": "fono" if table == "specialty" else "sala",
    }
    if table == "room":
        values["clinic_id"] = ids["clinic_id"]
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(connection, table, **values)
