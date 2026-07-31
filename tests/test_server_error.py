"""Server error (500) page and handler tests."""

from __future__ import annotations

import json
from collections.abc import Generator

import pytest
from app.config import get_settings
from app.dependencies import get_templates
from app.main import create_app
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

SECRET_MESSAGE = "SECRET_BOOM_SHOULD_NEVER_LEAK"
SECRET_PATH_HINT = "/Users/secret/clips/app/boom.py"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _json_ld(html: str) -> list[object]:
    return [
        json.loads(script.string or "")
        for script in _soup(html).find_all(
            "script",
            attrs={"type": "application/ld+json"},
        )
    ]


@pytest.fixture
def boom_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    """App with handlers + temporary boom route (not in production routers).

    create_app() calls register_exception_handlers(). APP_DEBUG=false matches
    production so ServerErrorMiddleware does not replace the branded 500 page.
    """
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("APP_BASE_URL", "http://testserver")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    get_settings.cache_clear()
    get_templates.cache_clear()
    app = create_app()

    @app.get("/__clips_test_boom")
    def boom() -> None:
        raise RuntimeError(f"{SECRET_MESSAGE} at {SECRET_PATH_HINT}")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    get_settings.cache_clear()
    get_templates.cache_clear()


def test_server_error_html_branded_page(boom_client: TestClient) -> None:
    response = boom_client.get(
        "/__clips_test_boom",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 500
    assert "text/html" in response.headers.get("content-type", "")

    html = response.text
    soup = _soup(html)

    assert "500" in html
    assert "일시적인 오류가 발생했습니다." in html
    assert "요청을 처리하는 중 문제가 발생했습니다" in html

    home_link = soup.select_one("a.not-found-actions__home")
    assert home_link is not None
    assert "홈" in home_link.get_text()
    assert soup.select_one("[data-error-back]") is not None
    assert soup.select_one(".not-found-hero") is not None
    assert "errors.css" in html

    assert SECRET_MESSAGE not in html
    assert SECRET_PATH_HINT not in html
    assert "RuntimeError" not in html
    assert "Traceback (most recent call last)" not in html
    assert 'File "' not in html

    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    content = robots.get("content") or ""
    assert "noindex" in content
    assert "nofollow" in content
    assert soup.find("link", attrs={"rel": "canonical"}) is None
    assert soup.find("meta", attrs={"property": "og:url"}) is None
    assert _json_ld(html) == []

    labels = [a.get_text(strip=True) for a in soup.select(".not-found-links__button")]
    assert labels == ["홈", "소식", "클래스", "아이템", "보스", "지도", "공략", "쿠폰"]


def test_server_error_json_accept_is_plain(boom_client: TestClient) -> None:
    response = boom_client.get(
        "/__clips_test_boom",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert SECRET_MESSAGE not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text


def test_server_error_plain_accept_is_plain(boom_client: TestClient) -> None:
    response = boom_client.get(
        "/__clips_test_boom",
        headers={"Accept": "text/plain"},
    )
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert SECRET_MESSAGE not in response.text
    assert "Traceback" not in response.text
