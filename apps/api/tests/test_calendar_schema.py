import pytest
from schema_support import catalog, insert
from sqlalchemy.exc import IntegrityError


def test_calendar_interval_and_exactly_one_person(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = catalog(connection, identity.tenant_id)
        common = {
            "tenant_id": identity.tenant_id,
            "starts_at": "2026-10-05T12:00:00Z",
            "ends_at": "2026-10-05T13:00:00Z",
            "reason": "Ausência",
            "created_by": identity.user_id,
        }
        insert(connection, "clinic_closure", **common, clinic_id=ids["clinic_id"])
        insert(connection, "person_block", **common, patient_id=ids["patient_id"])
        insert(connection, "person_block", **common, therapist_id=ids["therapist_id"])
    for changes in (
        {},
        {"patient_id": ids["patient_id"], "therapist_id": ids["therapist_id"]},
        {"patient_id": ids["patient_id"], "ends_at": "2026-10-05T12:00:00Z"},
    ):
        with pytest.raises(IntegrityError), admin_engine.begin() as connection:
            insert(connection, "person_block", **{**common, **changes})
