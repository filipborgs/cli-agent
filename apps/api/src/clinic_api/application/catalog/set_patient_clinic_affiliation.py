from uuid import UUID

from clinic_api.domain.catalog.patient_clinic import PatientClinic
from clinic_api.domain.catalog.ports import CatalogRepository
from clinic_api.domain.identity.context import AccessContext


class SetPatientClinicAffiliation:
    def __init__(self, repository: CatalogRepository, context: AccessContext) -> None:
        self._repository = repository
        self._context = context

    def execute(self, patient_id: UUID, clinic_id: UUID, active: bool) -> None:
        self._repository.add_patient_clinic(
            PatientClinic.create(self._context.tenant_id, patient_id, clinic_id, active)
        )
