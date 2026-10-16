from typing import assert_type

import pytest

from clinic_api.environment import EnvironmentVariable


@pytest.mark.parametrize("variable", list(EnvironmentVariable))
@pytest.mark.parametrize(
    "value", [None, "", "postgresql+psycopg://user:secret@db/clinic"]
)
def test_optional_environment(
    monkeypatch: pytest.MonkeyPatch, variable: EnvironmentVariable, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, value)
    assert variable.optional() == (value or None)


@pytest.mark.parametrize("variable", list(EnvironmentVariable))
@pytest.mark.parametrize(
    "value", [None, "", "postgresql+psycopg://user:secret@db/clinic"]
)
def test_required_environment(
    monkeypatch: pytest.MonkeyPatch, variable: EnvironmentVariable, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, value)
    if value:
        assert variable.required() == value
    else:
        other = next(item for item in EnvironmentVariable if item != variable)
        monkeypatch.setenv(
            other, "postgresql+psycopg://user:private-password@db/clinic"
        )
        with pytest.raises(ValueError) as error:
            variable.required()
        assert variable in str(error.value)
        assert "private-password" not in str(error.value)
        assert "postgresql" not in str(error.value)


def test_methods_read_changes_after_import(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in EnvironmentVariable:
        for value in ("first", "second"):
            monkeypatch.setenv(variable, value)
            assert variable.optional() == value
            assert variable.required() == value
        monkeypatch.delenv(variable)
        assert variable.optional() is None
        with pytest.raises(ValueError, match=variable):
            variable.required()


def test_string_values_preserve_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    variable = EnvironmentVariable.DATABASE_URL
    monkeypatch.setenv(variable, "  raw value  ")
    assert variable.required() == "  raw value  "
    assert variable.optional() == "  raw value  "
    assert variable.required(str) == "  raw value  "
    assert variable.optional(str) == "  raw value  "


@pytest.mark.parametrize("raw, expected", [("42", 42), (" -12 ", -12), ("0", 0)])
def test_integer_conversion(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: int
) -> None:
    variable = EnvironmentVariable.DATABASE_URL
    monkeypatch.setenv(variable, raw)
    assert variable.required(int) == expected
    assert variable.optional(int) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ],
)
def test_boolean_conversion(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool
) -> None:
    variable = EnvironmentVariable.MIGRATION_DATABASE_URL
    for value in (raw, f" \t{raw.upper()}\n", raw.title()):
        monkeypatch.setenv(variable, value)
        assert variable.required(bool) is expected
        assert variable.optional(bool) is expected


@pytest.mark.parametrize("value_type", [str, int, bool])
@pytest.mark.parametrize("raw", [None, ""])
def test_absent_typed_values(
    monkeypatch: pytest.MonkeyPatch,
    value_type: type[str] | type[int] | type[bool],
    raw: str | None,
) -> None:
    variable = EnvironmentVariable.DATABASE_URL
    if raw is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, raw)
    assert variable.optional(value_type) is None
    with pytest.raises(ValueError, match=variable):
        variable.required(value_type)


@pytest.mark.parametrize(
    "value_type, raw",
    [
        (int, "abc"),
        (int, "1.5"),
        (int, "0x10"),
        (bool, "private-secret"),
        (bool, "2"),
        (bool, " "),
    ],
)
def test_invalid_conversion_is_safe_for_both_methods(
    monkeypatch: pytest.MonkeyPatch,
    value_type: type[int] | type[bool],
    raw: str,
) -> None:
    import traceback

    variable = EnvironmentVariable.DATABASE_URL
    monkeypatch.setenv(variable, raw)
    for method in (variable.required, variable.optional):
        with pytest.raises(ValueError) as error:
            method(value_type)
        message = str(error.value)
        assert variable in message
        assert value_type.__name__ in message
        if raw.strip():
            assert raw not in message
        # Short tokens can occur incidentally in traceback line numbers.
        if len(raw.strip()) > 2:
            assert raw not in "".join(traceback.format_exception(error.value))


def test_static_return_types(monkeypatch: pytest.MonkeyPatch) -> None:
    variable = EnvironmentVariable.DATABASE_URL
    monkeypatch.setenv(variable, "1")
    assert_type(variable.required(), str)
    assert_type(variable.required(str), str)
    assert_type(variable.required(int), int)
    assert_type(variable.required(bool), bool)
    assert_type(variable.optional(), str | None)
    assert_type(variable.optional(str), str | None)
    assert_type(variable.optional(int), int | None)
    assert_type(variable.optional(bool), bool | None)
