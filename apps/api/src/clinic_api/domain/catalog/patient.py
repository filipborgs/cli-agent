from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Patient:
    id: UUID
    tenant_id: UUID
    name: str
    active: bool = True

    @classmethod
    def create(cls, tenant_id: UUID, name: str) -> "Patient":
        return cls(uuid4(), tenant_id, name)
