from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Specialty:
    id: UUID
    tenant_id: UUID
    name: str
    normalized_name: str
    active: bool = True
