from typing import Protocol

from clinic_api.domain.catalog.clinic import Clinic
from clinic_api.domain.catalog.patient import Patient
from clinic_api.domain.catalog.patient_clinic import PatientClinic


class CatalogRepository(Protocol):
    def add_clinic(self, clinic: Clinic) -> None: ...

    def add_patient(self, patient: Patient) -> None: ...

    def add_patient_clinic(self, affiliation: PatientClinic) -> None: ...
