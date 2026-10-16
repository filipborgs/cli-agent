import os
from enum import StrEnum
from typing import overload

_TRUE_TOKENS = frozenset({"true", "1", "yes", "on"})
_FALSE_TOKENS = frozenset({"false", "0", "no", "off"})


class EnvironmentVariable(StrEnum):
    DATABASE_URL = "DATABASE_URL"
    MIGRATION_DATABASE_URL = "MIGRATION_DATABASE_URL"

    @overload
    def optional(self, value_type: type[bool]) -> bool | None: ...

    @overload
    def optional(self, value_type: type[int]) -> int | None: ...

    @overload
    def optional(self, value_type: type[str] = str) -> str | None: ...

    def optional(
        self, value_type: type[str] | type[int] | type[bool] = str
    ) -> str | int | bool | None:
        value = os.environ.get(self)
        if not value:
            return None
        if value_type is str:
            return value
        if value_type is int:
            try:
                return int(value, 10)
            except ValueError:
                raise ValueError(f"{self} must be int") from None
        token = value.strip().lower()
        if token in _TRUE_TOKENS:
            return True
        if token in _FALSE_TOKENS:
            return False
        raise ValueError(f"{self} must be bool")

    @overload
    def required(self, value_type: type[bool]) -> bool: ...

    @overload
    def required(self, value_type: type[int]) -> int: ...

    @overload
    def required(self, value_type: type[str] = str) -> str: ...

    def required(
        self, value_type: type[str] | type[int] | type[bool] = str
    ) -> str | int | bool:
        value = self.optional(value_type)
        if value is None:
            raise ValueError(f"{self} is required")
        return value
