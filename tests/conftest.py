"""Pytest configuration."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "true")
os.environ.setdefault("APP_BASE_URL", "http://testserver")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def client() -> Generator[TestClient]:
    from app.config import get_settings
    from app.dependencies import get_templates
    from app.main import app

    get_settings.cache_clear()
    get_templates.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    get_templates.cache_clear()


@pytest.fixture
def local_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_BASE_URL", "http://testserver")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from app.config import get_settings
    from app.dependencies import get_templates
    from app.main import app

    get_settings.cache_clear()
    get_templates.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    get_templates.cache_clear()


@pytest.fixture
def production_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("APP_BASE_URL", "https://example.com")
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32chars")

    from app.config import get_settings
    from app.dependencies import get_templates
    from app.main import app

    get_settings.cache_clear()
    get_templates.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    get_templates.cache_clear()
    os.environ["APP_ENV"] = "test"
    os.environ["APP_DEBUG"] = "true"
    os.environ["APP_BASE_URL"] = "http://testserver"
    os.environ["SECRET_KEY"] = "test-secret-key"
    get_settings.cache_clear()
