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
    db_pool_size: int = 10

    # API keys
    openai_api_key: SecretStr
    nps_api_key: SecretStr

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url.startswith('postgresql://'):
            stripped_url = self.database_url.removeprefix('postgresql://')
            return 'postgresql+psycopg://' + stripped_url
        elif self.database_url.startswith('postgres://'):
            stripped_url = self.database_url.removeprefix('postgres://')
            return 'postgresql+psycopg://' + stripped_url
        else:
            return self.database_url



# reads and validates the environment once per process
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
