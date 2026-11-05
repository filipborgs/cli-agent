import pytest
from schema_support import appointment_values, insert, weekly
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError


def test_one_due_per_routine_and_no_child_due(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        original = insert(
            connection,
            "appointment",
            **appointment_values(ids, status="therapist_absent"),
        )
        values = {
            "tenant_id": ids["tenant_id"],
            "treatment_plan_id": ids["treatment_plan_id"],
            "original_appointment_id": original,
            "reason": "Ausência",
        }
        due = insert(connection, "replacement_due", **values)
        attempt = insert(
            connection,
            "appointment",
            **appointment_values(
                ids,
                origin="replacement",
                weekly_slot_id=None,
                occurrence_date=None,
                replacement_due_id=due,
            ),
        )
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(connection, "replacement_due", **values)
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(
            connection,
            "replacement_due",
            **{**values, "original_appointment_id": attempt},
        )
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        # An origin cannot be changed to replacement after a due references it.
        connection.execute(
            text(
                "UPDATE appointment SET origin='replacement', weekly_slot_id=NULL, occurrence_date=NULL, replacement_due_id=:due WHERE id=:original"
            ),
            {"due": due, "original": original},
        )


@pytest.mark.parametrize("status", ["scheduled", "completed"])
def test_one_attempt_per_reserved_result(factory, admin_engine, status):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        original = insert(
            connection,
            "appointment",
            **appointment_values(ids, status="therapist_absent"),
        )
        due = insert(
            connection,
            "replacement_due",
            tenant_id=ids["tenant_id"],
            treatment_plan_id=ids["treatment_plan_id"],
            original_appointment_id=original,
            reason="Ausência",
        )
        values = appointment_values(
            ids,
            origin="replacement",
            weekly_slot_id=None,
            occurrence_date=None,
            replacement_due_id=due,
            status=status,
        )
        insert(connection, "appointment", **values)
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(
            connection,
            "appointment",
            **{
                **values,
                "starts_at": "2026-10-12T12:00:00Z",
                "ends_at": "2026-10-12T12:30:00Z",
            },
        )


@pytest.mark.parametrize("status", ["scheduled", "completed"])
def test_concurrent_replacement_attempts_only_one_commits(
    factory, admin_engine, status
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        original = insert(
            connection,
            "appointment",
            **appointment_values(ids, status="therapist_absent"),
        )
        due = insert(
            connection,
            "replacement_due",
            tenant_id=identity.tenant_id,
            treatment_plan_id=ids["treatment_plan_id"],
            original_appointment_id=original,
            reason="Ausência",
        )
    barrier = Barrier(2)

    def attempt(day):
        try:
            with admin_engine.begin() as connection:
                barrier.wait(timeout=10)
                insert(
                    connection,
                    "appointment",
                    **appointment_values(
                        ids,
                        origin="replacement",
                        weekly_slot_id=None,
                        occurrence_date=None,
                        replacement_due_id=due,
                        status=status,
                        starts_at=f"2026-10-{day}T12:00:00Z",
                        ends_at=f"2026-10-{day}T12:30:00Z",
                    ),
                )
            return True
        except IntegrityError as error:
            assert error.orig.diag.constraint_name == f"uq_appointment_due_{status}"
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, day) for day in ("12", "19")]
        assert sorted(f.result(timeout=15) for f in futures) == [False, True]


def test_repeatable_read_origin_guard(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as c:
        ids = weekly(c, identity.tenant_id)
        first = insert(
            c, "appointment", **appointment_values(ids, status="therapist_absent")
        )
        second = insert(
            c,
            "appointment",
            **appointment_values(
                ids, status="therapist_absent", occurrence_date="2026-10-12"
            ),
        )
        other_due = insert(
            c,
            "replacement_due",
            tenant_id=identity.tenant_id,
            treatment_plan_id=ids["treatment_plan_id"],
            original_appointment_id=second,
            reason="seed",
        )
    with (
        admin_engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as changer,
        changer.begin(),
    ):
        changer.execute(text("SELECT count(*) FROM replacement_due")).scalar()
        with admin_engine.begin() as c:
            insert(
                c,
                "replacement_due",
                tenant_id=identity.tenant_id,
                treatment_plan_id=ids["treatment_plan_id"],
                original_appointment_id=first,
                reason="concurrent",
            )
        with pytest.raises(DBAPIError):
            changer.execute(
                text(
                    "UPDATE appointment SET origin='replacement', weekly_slot_id=NULL, occurrence_date=NULL, replacement_due_id=:due WHERE id=:id"
                ),
                {"due": other_due, "id": first},
            )
