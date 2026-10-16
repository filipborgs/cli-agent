from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Therapist:
    id: UUID
    tenant_id: UUID
    name: str
    active: bool = True
