from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Room:
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    name: str
    normalized_name: str
    active: bool = True
