from uuid import UUID

from clinic_api.domain.catalog.clinic import Clinic
from clinic_api.domain.catalog.ports import CatalogRepository
from clinic_api.domain.identity.context import AccessContext


class CreateClinic:
    def __init__(self, repository: CatalogRepository, context: AccessContext) -> None:
        self._repository = repository
        self._context = context

    def execute(self, name: str, timezone: str, default_duration_minutes: int) -> UUID:
        clinic = Clinic.create(
            self._context.tenant_id, name, timezone, default_duration_minutes
        )
        self._repository.add_clinic(clinic)
        return clinic.id
