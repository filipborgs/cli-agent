from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AccessContext:
    user_id: UUID
    tenant_id: UUID
