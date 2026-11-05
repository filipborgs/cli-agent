import pytest
from schema_support import weekly
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_slot_persists_and_rejects_wrong_clinic(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        assert (
            str(connection.scalar(text("SELECT valid_from FROM weekly_slot")))
            == "2026-10-01"
        )
    for field, value in (
        ("weekday", 7),
        ("duration_minutes", 0),
        ("valid_until", "2026-09-30"),
    ):
        with pytest.raises(IntegrityError), admin_engine.begin() as connection:
            connection.execute(
                text(f"UPDATE weekly_slot SET {field} = :value"), {"value": value}
            )
    from schema_support import insert

    with admin_engine.begin() as connection:
        other_clinic = insert(
            connection,
            "clinic",
            tenant_id=identity.tenant_id,
            name="Outra",
            timezone="UTC",
            default_duration_minutes=30,
        )
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE weekly_slot SET clinic_id = :clinic WHERE id = :weekly_slot_id"
            ),
            {**ids, "clinic": other_clinic},
        )
