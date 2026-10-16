from dataclasses import dataclass
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from clinic_api.domain.shared.errors import ValidationError


@dataclass(frozen=True)
class Clinic:
    id: UUID
    tenant_id: UUID
    name: str
    timezone: str
    default_duration_minutes: int
    active: bool = True

    @classmethod
    def create(
        cls, tenant_id: UUID, name: str, timezone: str, default_duration_minutes: int
    ) -> "Clinic":
        if default_duration_minutes <= 0:
            raise ValidationError("Clinic duration must be positive")
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as error:
            raise ValidationError("Clinic timezone is invalid") from error
        return cls(uuid4(), tenant_id, name, timezone, default_duration_minutes)
