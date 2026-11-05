"""SQL fixtures for persistence contracts, independent of application services."""

from uuid import UUID, uuid4

from sqlalchemy import Connection, text


def insert(connection: Connection, table: str, **values: object) -> UUID:
    identifier = values.setdefault("id", uuid4())
    columns = ", ".join(values)
    placeholders = ", ".join(f":{key}" for key in values)
    connection.execute(
        text(f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders})'), values
    )
    assert isinstance(identifier, UUID)
    return identifier


def catalog(
    connection: Connection, tenant_id: UUID, suffix: str = ""
) -> dict[str, UUID]:
    clinic = insert(
        connection,
        "clinic",
        tenant_id=tenant_id,
        name="Unidade",
        timezone="America/Bahia",
        default_duration_minutes=30,
    )
    patient = insert(connection, "patient", tenant_id=tenant_id, name="Paciente")
    therapist = insert(connection, "therapist", tenant_id=tenant_id, name="Terapeuta")
    specialty = insert(
        connection,
        "specialty",
        tenant_id=tenant_id,
        name="Fono" + suffix,
        normalized_name="fono" + suffix,
    )
    room = insert(
        connection,
        "room",
        tenant_id=tenant_id,
        clinic_id=clinic,
        name="Sala",
        normalized_name="sala",
    )
    for table, values in (
        ("patient_clinic", {"patient_id": patient, "clinic_id": clinic}),
        ("therapist_clinic", {"therapist_id": therapist, "clinic_id": clinic}),
        ("therapist_specialty", {"therapist_id": therapist, "specialty_id": specialty}),
        ("room_specialty", {"room_id": room, "specialty_id": specialty}),
    ):
        columns = ", ".join(["tenant_id", *values])
        params = {"tenant_id": tenant_id, **values}
        connection.execute(
            text(
                f"INSERT INTO {table} ({columns}) VALUES ({', '.join(':' + key for key in params)})"
            ),
            params,
        )
    return {
        "tenant_id": tenant_id,
        "clinic_id": clinic,
        "patient_id": patient,
        "therapist_id": therapist,
        "specialty_id": specialty,
        "room_id": room,
    }


def context(connection: Connection, tenant_id: UUID, user_id: UUID) -> None:
    connection.execute(
        text(
            "SELECT set_config('app.tenant_id', :tenant, true), set_config('app.user_id', :user, true)"
        ),
        {"tenant": str(tenant_id), "user": str(user_id)},
    )


def planning(connection: Connection, tenant_id: UUID) -> dict[str, UUID]:
    ids = catalog(connection, tenant_id)
    plan = insert(
        connection,
        "treatment_plan",
        tenant_id=tenant_id,
        patient_id=ids["patient_id"],
        therapist_id=ids["therapist_id"],
        specialty_id=ids["specialty_id"],
        sessions_per_week=2,
        valid_from="2026-10-01",
    )
    connection.execute(
        text(
            "INSERT INTO treatment_plan_clinic (tenant_id, treatment_plan_id, clinic_id) VALUES (:tenant_id, :plan, :clinic_id)"
        ),
        {**ids, "plan": plan},
    )
    return {**ids, "treatment_plan_id": plan}


def weekly(connection: Connection, tenant_id: UUID) -> dict[str, UUID]:
    ids = planning(connection, tenant_id)
    slot = insert(
        connection,
        "weekly_slot",
        tenant_id=tenant_id,
        treatment_plan_id=ids["treatment_plan_id"],
        clinic_id=ids["clinic_id"],
        room_id=ids["room_id"],
        weekday=0,
        start_time="09:00",
        duration_minutes=30,
        valid_from="2026-10-01",
    )
    return {**ids, "weekly_slot_id": slot}


def appointment_values(ids: dict[str, UUID], **overrides: object) -> dict[str, object]:
    return {
        **ids,
        "starts_at": "2026-10-05T12:00:00Z",
        "ends_at": "2026-10-05T12:30:00Z",
        "duration_minutes": 30,
        "origin": "routine",
        "status": "scheduled",
        "occurrence_date": "2026-10-05",
        **overrides,
    }


def full_schema(connection: Connection, identity) -> dict[str, dict[str, object]]:
    """One row of every table in a tenant, with legitimate parent references."""
    ids = weekly(connection, identity.tenant_id)
    interval = {
        "tenant_id": identity.tenant_id,
        "starts_at": "2026-10-05T12:00:00Z",
        "ends_at": "2026-10-05T13:00:00Z",
        "reason": "Fechamento",
        "created_by": identity.user_id,
    }
    insert(connection, "clinic_closure", **interval, clinic_id=ids["clinic_id"])
    insert(connection, "person_block", **interval, patient_id=ids["patient_id"])
    for table, person in (
        ("patient_availability", "patient_id"),
        ("therapist_availability", "therapist_id"),
        ("clinic_hours", None),
    ):
        values = {
            "tenant_id": identity.tenant_id,
            "clinic_id": ids["clinic_id"],
            "weekday": 0,
            "start_time": "08:00",
            "end_time": "17:00",
            "valid_from": "2026-10-01",
        }
        if person:
            values[person] = ids[person]
        insert(connection, table, **values)
    original = insert(
        connection, "appointment", **appointment_values(ids, status="therapist_absent")
    )
    insert(
        connection,
        "replacement_due",
        tenant_id=identity.tenant_id,
        treatment_plan_id=ids["treatment_plan_id"],
        original_appointment_id=original,
        reason="Ausência",
    )
    connection.execute(
        text(
            'INSERT INTO appointment_event (id, tenant_id, appointment_id, actor_id, kind, before, after) VALUES (:id, :tenant, :appointment, :actor, \'absence\', \'{"status":"scheduled"}\'::jsonb, \'{"status":"therapist_absent"}\'::jsonb)'
        ),
        {
            "id": uuid4(),
            "tenant": identity.tenant_id,
            "appointment": original,
            "actor": identity.user_id,
        },
    )
    agenda = insert(
        connection,
        "monthly_agenda",
        tenant_id=identity.tenant_id,
        clinic_id=ids["clinic_id"],
        month="2026-10-01",
    )
    run = insert(
        connection,
        "generation_run",
        tenant_id=identity.tenant_id,
        monthly_agenda_id=agenda,
    )
    insert(
        connection,
        "generation_deficit",
        tenant_id=identity.tenant_id,
        generation_run_id=run,
        treatment_plan_id=ids["treatment_plan_id"],
        week_start="2026-10-05",
        missing_count=1,
        reason_code="no_common_availability",
    )
    from sqlalchemy import inspect

    tables = set(inspect(connection).get_table_names()) - {
        "tenant",
        "user",
        "user_tenant",
        "alembic_version",
    }
    return {
        table: dict(
            connection.execute(
                text(f"SELECT * FROM {table} WHERE tenant_id=:tenant"),
                {"tenant": identity.tenant_id},
            )
            .mappings()
            .one()
        )
        for table in tables
    }
