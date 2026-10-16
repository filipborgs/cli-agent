import pytest

from clinic_api.environment import EnvironmentVariable


def test_runtime_settings_do_not_require_migration_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from clinic_api.settings import Settings

    monkeypatch.setenv(
        EnvironmentVariable.DATABASE_URL,
        "postgresql+psycopg://runtime@localhost/clinic",
    )
    monkeypatch.delenv(EnvironmentVariable.MIGRATION_DATABASE_URL, raising=False)
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://runtime@localhost/clinic"
    assert settings.migration_database_url is None


def test_settings_read_separate_migration_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from clinic_api.settings import Settings

    monkeypatch.setenv(
        EnvironmentVariable.DATABASE_URL,
        "postgresql+psycopg://runtime@localhost/clinic",
    )
    monkeypatch.setenv(
        EnvironmentVariable.MIGRATION_DATABASE_URL,
        "postgresql+psycopg://migrator@localhost/clinic",
    )
    assert Settings().migration_database_url == (
        "postgresql+psycopg://migrator@localhost/clinic"
    )


def test_missing_runtime_url_fails_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    from clinic_api.settings import Settings

    monkeypatch.delenv(EnvironmentVariable.DATABASE_URL, raising=False)
    with pytest.raises(ValueError, match=EnvironmentVariable.DATABASE_URL):
        Settings()


def test_explicit_settings_without_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from dataclasses import FrozenInstanceError

    from clinic_api.environment import EnvironmentVariable
    from clinic_api.settings import Settings

    for variable in EnvironmentVariable:
        monkeypatch.delenv(variable, raising=False)
    settings = Settings(
        database_url="explicit-runtime", migration_database_url="explicit-admin"
    )
    assert settings.database_url == "explicit-runtime"
    assert settings.migration_database_url == "explicit-admin"
    assert Settings(database_url="explicit-runtime").migration_database_url is None
    with pytest.raises(FrozenInstanceError):
        settings.database_url = "changed"


def test_api_health_import_without_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    import sys

    from clinic_api.environment import EnvironmentVariable

    for variable in EnvironmentVariable:
        monkeypatch.delenv(variable, raising=False)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastapi.testclient import TestClient; from clinic_api.main import app; assert TestClient(app).get('/api/health').json() == {'status': 'ok'}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
