from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PatientClinic:
    tenant_id: UUID
    patient_id: UUID
    clinic_id: UUID
    active: bool

    @classmethod
    def create(
        cls, tenant_id: UUID, patient_id: UUID, clinic_id: UUID, active: bool
    ) -> "PatientClinic":
        return cls(tenant_id, patient_id, clinic_id, active)
