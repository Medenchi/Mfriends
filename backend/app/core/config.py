from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MFriends"
    app_env: str = "development"
    app_base_url: str = "http://127.0.0.1:8000/mfriends"
    api_base_url: str = "http://127.0.0.1:8000/api"
    secret_key: str = Field(default="dev-only-change-me", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 45
    refresh_token_expire_days: int = 30
    database_path: Path = Path("data/mfriends.sqlite3")
    upload_dir: Path = Path("uploads")
    max_upload_size_bytes: int = 5 * 1024 * 1024
    allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "mail@malinacode.is-a.dev"
    smtp_tls: bool = True
    moderation_provider: str = "disabled"
    moderation_api_url: str = ""
    moderation_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
