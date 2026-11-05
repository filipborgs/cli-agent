from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from schema_support import appointment_values, insert, weekly
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_occurrence_identity_survives_move_and_cancel(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        insert(connection, "appointment", **appointment_values(ids, status="cancelled"))
        connection.execute(
            text(
                "UPDATE appointment SET starts_at = starts_at + interval '1 day', ends_at = ends_at + interval '1 day'"
            )
        )
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(connection, "appointment", **appointment_values(ids))


@pytest.mark.parametrize(
    "status",
    [
        "scheduled",
        "completed",
        "cancelled",
        "patient_absent",
        "therapist_absent",
        "dispensed",
    ],
)
def test_only_reserved_states_block_intervals(factory, admin_engine, status):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        insert(connection, "appointment", **appointment_values(ids, status=status))

    def create():
        with admin_engine.begin() as connection:
            insert(
                connection,
                "appointment",
                **appointment_values(ids, occurrence_date="2026-10-12"),
            )

    if status in ("scheduled", "completed"):
        with pytest.raises(IntegrityError):
            create()
    else:
        create()
    with admin_engine.begin() as connection:
        insert(
            connection,
            "appointment",
            **appointment_values(
                ids,
                occurrence_date="2026-10-19",
                starts_at="2026-10-05T12:30:00Z",
                ends_at="2026-10-05T13:00:00Z",
            ),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "invalid"},
        {"origin": "invalid"},
        {"ends_at": "2026-10-05T12:00:00Z"},
        {"duration_minutes": 0},
        {"replacement_decision": "invalid"},
    ],
)
def test_invalid_session_data_rejected(factory, admin_engine, changes):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(connection, "appointment", **appointment_values(ids, **changes))


def test_concurrent_reservation_only_one_commits(factory, admin_engine):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
    barrier = Barrier(2)

    def reserve(day):
        try:
            with admin_engine.begin() as connection:
                barrier.wait(timeout=10)
                insert(
                    connection,
                    "appointment",
                    **appointment_values(ids, occurrence_date=day),
                )
            return True
        except IntegrityError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(reserve, day) for day in ("2026-10-05", "2026-10-12")]
        assert sorted(f.result(timeout=15) for f in futures) == [False, True]


def test_inactive_qualification_blocks_new_reservation_keeps_history(
    factory, admin_engine
):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        insert(connection, "appointment", **appointment_values(ids))
        connection.execute(text("UPDATE therapist_specialty SET active = false"))
        assert connection.scalar(text("SELECT count(*) FROM appointment")) == 1
    with pytest.raises(IntegrityError), admin_engine.begin() as connection:
        insert(
            connection,
            "appointment",
            **appointment_values(
                ids,
                occurrence_date="2026-10-12",
                starts_at="2026-10-12T12:00:00Z",
                ends_at="2026-10-12T12:30:00Z",
            ),
        )


@pytest.mark.parametrize("resource", ["patient_id", "therapist_id", "room_id"])
def test_independent_resource_exclusions_across_clinics(
    factory, admin_engine, resource
):
    from schema_support import catalog

    identity = factory.identity()
    with admin_engine.begin() as connection:
        first = weekly(connection, identity.tenant_id)
        other = catalog(connection, identity.tenant_id, suffix="2")
        other[resource] = first[resource]
        if resource == "room_id":
            other["clinic_id"] = first["clinic_id"]
        # Qualify only the intended resources for the second plan and clinic.
        for table, fields in (
            ("patient_clinic", ("patient_id", "clinic_id")),
            ("therapist_clinic", ("therapist_id", "clinic_id")),
            ("therapist_specialty", ("therapist_id", "specialty_id")),
            ("room_specialty", ("room_id", "specialty_id")),
        ):
            connection.execute(
                text(
                    f"INSERT INTO {table} (tenant_id, {', '.join(fields)}) VALUES (:tenant_id, {', '.join(':' + key for key in fields)}) ON CONFLICT DO NOTHING"
                ),
                other,
            )
        plan = insert(
            connection,
            "treatment_plan",
            **{
                key: other[key]
                for key in ("tenant_id", "patient_id", "therapist_id", "specialty_id")
            },
            sessions_per_week=1,
            valid_from="2026-10-01",
        )
        connection.execute(
            text(
                "INSERT INTO treatment_plan_clinic (tenant_id, treatment_plan_id, clinic_id) VALUES (:tenant_id, :plan, :clinic_id)"
            ),
            {**other, "plan": plan},
        )
        slot = insert(
            connection,
            "weekly_slot",
            tenant_id=identity.tenant_id,
            treatment_plan_id=plan,
            clinic_id=other["clinic_id"],
            room_id=other["room_id"],
            weekday=0,
            start_time="09:00",
            duration_minutes=30,
            valid_from="2026-10-01",
        )
        second = {**other, "treatment_plan_id": plan, "weekly_slot_id": slot}
        insert(connection, "appointment", **appointment_values(first))
    with pytest.raises(IntegrityError) as caught, admin_engine.begin() as connection:
        insert(connection, "appointment", **appointment_values(second))
    assert (
        caught.value.orig.diag.constraint_name
        == f"ex_appointment_{resource.removesuffix('_id')}"
    )


@pytest.mark.parametrize(
    "table",
    [
        "patient_clinic",
        "therapist_clinic",
        "therapist_specialty",
        "room_specialty",
        "treatment_plan_clinic",
        "clinic",
        "patient",
        "therapist",
        "specialty",
        "room",
    ],
)
def test_all_resource_qualifications_required_for_new_reservation(
    factory, admin_engine, table
):
    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
        connection.execute(text(f"UPDATE {table} SET active=false"))
    with pytest.raises(IntegrityError) as caught, admin_engine.begin() as connection:
        insert(connection, "appointment", **appointment_values(ids))
    assert caught.value.orig.sqlstate == "23514"


def test_qualification_change_waits_for_reservation(factory, admin_engine):
    import time
    from queue import Queue

    identity = factory.identity()
    with admin_engine.begin() as connection:
        ids = weekly(connection, identity.tenant_id)
    pid_queue = Queue()

    def disable():
        with admin_engine.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout='10s'"))
            pid_queue.put(connection.scalar(text("SELECT pg_backend_pid()")))
            connection.execute(text("UPDATE therapist_specialty SET active=false"))

    with ThreadPoolExecutor(max_workers=1) as pool:
        with admin_engine.begin() as connection:
            reservation_pid = connection.scalar(text("SELECT pg_backend_pid()"))
            insert(connection, "appointment", **appointment_values(ids))
            future = pool.submit(disable)
            disable_pid = pid_queue.get(timeout=10)
            deadline = time.monotonic() + 5
            blockers = []
            with admin_engine.connect() as observer:
                while time.monotonic() < deadline:
                    blockers = observer.scalar(
                        text("SELECT pg_blocking_pids(:pid)"), {"pid": disable_pid}
                    )
                    if reservation_pid in blockers:
                        break
                    time.sleep(0.01)
            assert reservation_pid in blockers
        future.result(timeout=10)
    with admin_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM appointment")) == 1
        assert (
            connection.scalar(text("SELECT active FROM therapist_specialty")) is False
        )
