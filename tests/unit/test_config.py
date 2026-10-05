"""Tests for the application settings."""

import pytest
from pytest import MonkeyPatch

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Clear the settings cache before each test so no stale instance is reused."""
    get_settings.cache_clear()


def test_database_url_defaults_to_project_data_directory(
    monkeypatch: MonkeyPatch,
) -> None:
    """The default database URL points to the data directory inside the project."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    # pydantic-settings' internal init kwargs aren't visible to mypy (dataclass_transform)

    assert settings.database_url.startswith("sqlite:///")
    assert settings.database_url.endswith("/data/recipe_drawer.db")


def test_database_url_uses_forward_slashes(monkeypatch: MonkeyPatch) -> None:
    """The default database URL contains no backslashes, which SQLAlchemy cannot parse."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    # pydantic-settings' internal init kwargs aren't visible to mypy (dataclass_transform)

    assert "\\" not in settings.database_url


def test_environment_variable_overrides_default(monkeypatch: MonkeyPatch) -> None:
    """An environment variable takes precedence over the field default."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/test.db")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    # pydantic-settings' internal init kwargs aren't visible to mypy (dataclass_transform)

    assert settings.database_url == "sqlite:///tmp/test.db"


def test_get_settings_returns_the_same_instance() -> None:
    """get_settings() is cached and returns the same object on every call."""
    assert get_settings() is get_settings()


def test_unrelated_env_var_is_ignored(monkeypatch: MonkeyPatch) -> None:
    """An environment variable outside the Settings schema does not raise."""
    monkeypatch.setenv("SOME_UNRELATED_VAR", "value")

    Settings(_env_file=None)  # type: ignore[call-arg]
    # pydantic-settings' internal init kwargs aren't visible to mypy (dataclass_transform)
