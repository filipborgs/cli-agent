import pytest
from schema_support import insert, planning
from sqlalchemy.exc import IntegrityError


def test_monthly_agenda_identity_and_generation_data(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = planning(connection, identity.tenant_id)
        values = {
            "tenant_id": identity.tenant_id,
            "clinic_id": ids["clinic_id"],
            "month": "2026-10-01",
        }
        agenda = insert(connection, "monthly_agenda", **values)
        run = insert(
            connection,
            "generation_run",
            tenant_id=identity.tenant_id,
            monthly_agenda_id=agenda,
        )
        deficit = {
            "tenant_id": identity.tenant_id,
            "generation_run_id": run,
            "treatment_plan_id": ids["treatment_plan_id"],
            "week_start": "2026-10-05",
            "missing_count": 1,
            "reason_code": "no_common_availability",
        }
        insert(connection, "generation_deficit", **deficit)
    for changes in ({}, {"month": "2026-11-02"}):
        with pytest.raises(IntegrityError), admin_engine.begin() as connection:
            insert(connection, "monthly_agenda", **{**values, **changes})
    for changes in (
        {"missing_count": 0},
        {"reason_code": "invalid"},
        {"week_start": "2026-10-06"},
    ):
        with pytest.raises(IntegrityError), admin_engine.begin() as connection:
            insert(connection, "generation_deficit", **{**deficit, **changes})
