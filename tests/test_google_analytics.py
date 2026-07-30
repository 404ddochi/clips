"""Google Analytics 4 (gtag.js) integration tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


@pytest.fixture
def ga_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_BASE_URL", "http://testserver")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_ANALYTICS_ID", "G-TP9RLEBSLM")

    from app.config import get_settings
    from app.dependencies import get_templates
    from app.main import app

    get_settings.cache_clear()
    get_templates.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    get_templates.cache_clear()


def test_ga_script_present_when_configured(ga_client: TestClient) -> None:
    html = ga_client.get("/").text
    assert "googletagmanager.com/gtag/js?id=G-TP9RLEBSLM" in html
    assert "G-TP9RLEBSLM" in html
    assert 'gtag("config"' in html
    assert html.count("googletagmanager.com/gtag/js") == 1
    soup = _soup(html)
    scripts = soup.find_all("script")
    external = [
        tag
        for tag in scripts
        if tag.get("src") and "googletagmanager.com/gtag/js" in tag.get("src", "")
    ]
    assert len(external) == 1
    assert "G-TP9RLEBSLM" in (external[0].get("src") or "")
    inline = "\n".join(tag.string or "" for tag in scripts if tag.string)
    assert "G-TP9RLEBSLM" in inline
    assert "dataLayer" in inline


def test_ga_absent_when_unset(client: TestClient) -> None:
    html = client.get("/").text
    assert "googletagmanager.com/gtag/js" not in html
    assert "gtag(" not in html
    assert "G-TP9RLEBSLM" not in html
    soup = _soup(html)
    # Measurement ID must not leak into meta/canonical/OG
    for meta in soup.find_all("meta"):
        content = meta.get("content") or ""
        assert "G-TP9RLEBSLM" not in content
        assert "googletagmanager" not in content


def test_ga_settings_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_ANALYTICS_ID", "  G-TP9RLEBSLM  ")
    from app.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()
    assert settings.google_analytics_id == "G-TP9RLEBSLM"
    get_settings.cache_clear()
