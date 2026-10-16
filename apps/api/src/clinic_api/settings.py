from dataclasses import dataclass, field

from clinic_api.environment import EnvironmentVariable


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=EnvironmentVariable.DATABASE_URL.required)
    migration_database_url: str | None = field(
        default_factory=EnvironmentVariable.MIGRATION_DATABASE_URL.optional
    )
