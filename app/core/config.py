"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration read from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        f"sqlite:///{(BASE_DIR / 'data' / 'recipe_drawer.db').as_posix()}"
    )


@lru_cache
def get_settings() -> Settings:
    """Return the application settings, loaded once and cached.

    Returns:
        The validated Settings instance built from environment variables.
    """
    return Settings()
