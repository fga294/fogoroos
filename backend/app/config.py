"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MariaDB / MySQL connection string, e.g.
    # mysql+pymysql://user:pass@127.0.0.1:3306/u14_stats?charset=utf8mb4
    database_url: str = "mysql+pymysql://u14:u14secret@127.0.0.1:3306/u14_stats?charset=utf8mb4"

    # HTTP Basic Auth for mutating API routes (set strong values in production)
    admin_username: str = "coach"
    admin_password: str = "change-me-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
