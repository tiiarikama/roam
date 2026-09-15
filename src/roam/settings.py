from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # db
    database_url: str

    # API keys
    openai_api_key: SecretStr
    nps_api_key: SecretStr


# reads and validates the environment once per process
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
