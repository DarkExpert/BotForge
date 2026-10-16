from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    telegram_bot_alpha_token: str | None = None
    telegram_bot_beta_token: str | None = None
    admin_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
