"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me"
AppEnv = Literal["local", "development", "staging", "production", "prod", "test"]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="CLIPS", alias="APP_NAME")
    app_env: AppEnv = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_base_url: str = Field(default="http://127.0.0.1:8000", alias="APP_BASE_URL")
    secret_key: str = Field(default=DEFAULT_SECRET_KEY, alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./clips.db", alias="DATABASE_URL")
    default_locale: str = Field(default="ko", alias="DEFAULT_LOCALE")
    timezone: str = Field(default="Asia/Seoul", alias="TIMEZONE")

    @field_validator("app_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    def is_production(self) -> bool:
        return self.app_env in ("production", "prod")

    def is_debug_enabled(self) -> bool:
        if self.is_production():
            return self.app_debug
        return self.app_debug

    def absolute_url(self, path: str = "/") -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.app_base_url}{path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_settings(settings: Settings) -> None:
    """Block startup when production uses insecure defaults."""
    if not settings.is_production():
        return
    if settings.secret_key == DEFAULT_SECRET_KEY:
        msg = "운영 환경에서는 SECRET_KEY를 기본값(change-me)으로 사용할 수 없습니다."
        raise RuntimeError(msg)
    if settings.app_debug:
        msg = "운영 환경에서는 APP_DEBUG를 true로 설정하지 마세요."
        raise RuntimeError(msg)
