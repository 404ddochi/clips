"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me"
AppEnv = Literal["local", "development", "staging", "production", "prod", "test"]


def normalize_site_url(value: str) -> str:
    """Strip whitespace and trailing slashes from the site origin."""
    return value.strip().rstrip("/")


def normalize_canonical_path(path: str) -> str:
    """Normalize a path for canonical/sitemap URLs (no query/fragment)."""
    if path.startswith("http://") or path.startswith("https://"):
        parts = urlsplit(path)
        path = parts.path or "/"
    path = path.split("?", 1)[0].split("#", 1)[0].strip() or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    # Collapse duplicate slashes in the path portion only.
    while "//" in path:
        path = path.replace("//", "/")
    return path or "/"


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="CLIPS", alias="APP_NAME")
    app_env: AppEnv = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8001, alias="APP_PORT")
    # Prefer SITE_URL; APP_BASE_URL remains supported for compatibility.
    # Production fallback origin when env is unset (local .env should override).
    app_base_url: str = Field(
        default="https://playclips.kr",
        validation_alias=AliasChoices("SITE_URL", "APP_BASE_URL"),
        serialization_alias="SITE_URL",
    )
    secret_key: str = Field(default=DEFAULT_SECRET_KEY, alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./clips.db", alias="DATABASE_URL")
    default_locale: str = Field(default="ko", alias="DEFAULT_LOCALE")
    timezone: str = Field(default="Asia/Seoul", alias="TIMEZONE")

    @field_validator("app_base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        return normalize_site_url(value)

    @property
    def site_url(self) -> str:
        """Canonical site origin (SITE_URL / APP_BASE_URL)."""
        return self.app_base_url

    def is_production(self) -> bool:
        return self.app_env in ("production", "prod")

    def is_staging(self) -> bool:
        return self.app_env == "staging"

    def is_design_system_enabled(self) -> bool:
        """Dev-only CDL showcase: local / development."""
        return self.app_env in ("local", "development")

    def allows_demo_content(self) -> bool:
        """Mock news/coupons/patches — never on production public surfaces."""
        return not self.is_production()

    def is_debug_enabled(self) -> bool:
        if self.is_production():
            return self.app_debug
        return self.app_debug

    def absolute_url(self, path: str = "/") -> str:
        if path.startswith("http://") or path.startswith("https://"):
            parts = urlsplit(path)
            normalized = normalize_canonical_path(parts.path or "/")
            return urlunsplit((parts.scheme, parts.netloc, normalized, "", ""))
        normalized = normalize_canonical_path(path)
        return f"{self.app_base_url}{normalized}"

    def canonical_url(self, path: str = "/") -> str:
        """SITE_URL + normalized path (no query/fragment)."""
        return self.absolute_url(path)


_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1"})


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_settings(settings: Settings) -> None:
    """Block startup when production uses insecure defaults or bad SITE_URL."""
    if not settings.is_production():
        return
    if settings.secret_key == DEFAULT_SECRET_KEY:
        msg = "운영 환경에서는 SECRET_KEY를 기본값(change-me)으로 사용할 수 없습니다."
        raise RuntimeError(msg)
    if settings.app_debug:
        msg = "운영 환경에서는 APP_DEBUG를 true로 설정하지 마세요."
        raise RuntimeError(msg)
    parts = urlsplit(settings.site_url)
    if parts.scheme != "https":
        msg = "운영 환경 SITE_URL은 https:// 절대 URL이어야 합니다."
        raise RuntimeError(msg)
    host = (parts.hostname or "").casefold()
    if not host or host in _LOCAL_HOSTS or host.endswith(".local"):
        msg = "운영 환경 SITE_URL에 localhost 또는 루프백 호스트를 사용할 수 없습니다."
        raise RuntimeError(msg)
