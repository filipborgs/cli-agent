from uuid import UUID

from clinic_api.domain.catalog.patient import Patient
from clinic_api.domain.catalog.ports import CatalogRepository
from clinic_api.domain.identity.context import AccessContext


class CreatePatient:
    def __init__(self, repository: CatalogRepository, context: AccessContext) -> None:
        self._repository = repository
        self._context = context

    def execute(self, name: str) -> UUID:
        patient = Patient.create(self._context.tenant_id, name)
        self._repository.add_patient(patient)
        return patient.id
