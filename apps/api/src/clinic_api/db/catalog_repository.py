from clinic_api.db.models.catalog.entities import (
    Clinic as ClinicModel,
)
from clinic_api.db.models.catalog.entities import (
    Patient as PatientModel,
)
from clinic_api.db.models.catalog.entities import (
    PatientClinic as PatientClinicModel,
)
from clinic_api.db.session import TenantSession
from clinic_api.domain.catalog.clinic import Clinic
from clinic_api.domain.catalog.patient import Patient
from clinic_api.domain.catalog.patient_clinic import PatientClinic


class SqlAlchemyCatalogRepository:
    def __init__(self, session: TenantSession) -> None:
        self._session = session

    def add_clinic(self, clinic: Clinic) -> None:
        self._session.add(ClinicModel(**clinic.__dict__))
        self._session.flush()

    def add_patient(self, patient: Patient) -> None:
        self._session.add(PatientModel(**patient.__dict__))
        self._session.flush()

    def add_patient_clinic(self, affiliation: PatientClinic) -> None:
        self._session.add(PatientClinicModel(**affiliation.__dict__))
        self._session.flush()
