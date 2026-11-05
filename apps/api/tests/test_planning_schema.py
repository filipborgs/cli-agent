import pytest
from schema_support import catalog, insert, planning
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_plan_validity_exclusion_and_adjacent_periods(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = planning(connection, identity.tenant_id)
        connection.execute(text("UPDATE treatment_plan SET valid_until = '2026-10-31'"))
        values = {
            key: ids[key]
            for key in ("tenant_id", "patient_id", "therapist_id", "specialty_id")
        }
        insert(
            connection,
            "treatment_plan",
            **values,
            sessions_per_week=1,
            valid_from="2026-11-01",
        )
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(
            connection,
            "treatment_plan",
            **values,
            sessions_per_week=1,
            valid_from="2026-10-31",
            valid_until="2026-10-31",
        )


@pytest.mark.parametrize(
    "overrides",
    [{"sessions_per_week": 0}, {"duration_minutes": 0}, {"valid_until": "2026-09-30"}],
)
def test_invalid_plan_values_rejected(factory, admin_engine, overrides):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = catalog(connection, identity.tenant_id)
    values = {
        key: ids[key]
        for key in ("tenant_id", "patient_id", "therapist_id", "specialty_id")
    }
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(
            connection,
            "treatment_plan",
            **{
                **values,
                "sessions_per_week": 1,
                "valid_from": "2026-10-01",
                **overrides,
            },
        )


@pytest.mark.parametrize(
    "table,person",
    [
        ("patient_availability", "patient_id"),
        ("therapist_availability", "therapist_id"),
        ("clinic_hours", None),
    ],
)
def test_availability_windows_and_checks(factory, admin_engine, table, person):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = planning(connection, identity.tenant_id)
        values = {
            "tenant_id": ids["tenant_id"],
            "clinic_id": ids["clinic_id"],
            "weekday": 0,
            "valid_from": "2026-10-01",
        }
        if person:
            values[person] = ids[person]
        insert(connection, table, **values, start_time="08:00", end_time="12:00")
        insert(connection, table, **values, start_time="13:00", end_time="17:00")
        assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 2
    for changes in (
        {"weekday": 7},
        {"start_time": "18:00"},
        {"valid_until": "2026-09-30"},
    ):
        with pytest.raises(IntegrityError), admin_engine.begin() as connection:
            insert(
                connection,
                table,
                **{**values, "start_time": "08:00", "end_time": "12:00", **changes},
            )
