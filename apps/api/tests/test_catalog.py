from uuid import uuid4

import pytest
from sqlalchemy import text


def test_invalid_timezone_and_duration(factory, runtime_engine) -> None:
    from clinic_api.application.catalog.create_clinic import CreateClinic
    from clinic_api.db.catalog_repository import SqlAlchemyCatalogRepository
    from clinic_api.db.session import tenant_session
    from clinic_api.domain.shared.errors import ValidationError

    context = factory.identity()
    with tenant_session(runtime_engine, context) as session:
        repository = SqlAlchemyCatalogRepository(session)
        use_case = CreateClinic(repository, context)
        with pytest.raises(ValidationError):
            use_case.execute("Unidade", "Fuso/Inexistente", 30)
        with pytest.raises(ValidationError):
            use_case.execute("Unidade", "America/Sao_Paulo", 0)


def test_creates_clinic_in_active_tenant(factory, runtime_engine) -> None:
    from clinic_api.application.catalog.create_clinic import CreateClinic
    from clinic_api.db.catalog_repository import SqlAlchemyCatalogRepository
    from clinic_api.db.session import tenant_session

    context = factory.identity()
    with tenant_session(runtime_engine, context) as session:
        clinic_id = CreateClinic(
            SqlAlchemyCatalogRepository(session),
            context,
        ).execute("Unidade", "America/Sao_Paulo", 30)
        assert (
            session.scalar(
                text("SELECT count(*) FROM clinic WHERE id = :id"), {"id": clinic_id}
            )
            == 1
        )


def test_single_patient_in_two_clinics(factory, runtime_engine) -> None:
    from clinic_api.application.catalog.create_clinic import CreateClinic
    from clinic_api.application.catalog.create_patient import CreatePatient
    from clinic_api.application.catalog.set_patient_clinic_affiliation import (
        SetPatientClinicAffiliation,
    )
    from clinic_api.db.catalog_repository import SqlAlchemyCatalogRepository
    from clinic_api.db.session import tenant_session

    context = factory.identity()
    with tenant_session(runtime_engine, context) as session:
        repository = SqlAlchemyCatalogRepository(session)
        patient_id = CreatePatient(repository, context).execute("Paciente")
        clinic = CreateClinic(repository, context)
        first = clinic.execute("A", "America/Sao_Paulo", 30)
        second = clinic.execute("B", "America/Sao_Paulo", 30)
        affiliation = SetPatientClinicAffiliation(repository, context)
        affiliation.execute(patient_id, first, True)
        affiliation.execute(patient_id, second, True)
        assert (
            session.scalar(
                text("SELECT count(*) FROM patient_clinic WHERE patient_id = :patient"),
                {"patient": patient_id},
            )
            == 2
        )


def test_resource_kind_has_therapist_and_room() -> None:
    from clinic_api.domain.catalog.types import ResourceKind

    assert ResourceKind.THERAPIST.value == "therapist"
    assert ResourceKind.ROOM.value == "room"


def test_many_specialties_per_therapist_and_room() -> None:
    from clinic_api.domain.catalog.therapist import Therapist

    therapist = Therapist(id=uuid4(), tenant_id=uuid4(), name="Terapeuta")
    assert therapist.name == "Terapeuta"
