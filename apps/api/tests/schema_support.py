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
