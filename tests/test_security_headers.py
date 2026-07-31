"""Security HTTP header regression tests."""

from __future__ import annotations

import pytest
from app.config import get_settings
from app.dependencies import get_templates
from app.main import create_app
from fastapi.testclient import TestClient

_PERMISSIONS_REQUIRED = (
    "geolocation=()",
    "microphone=()",
    "camera=()",
    "payment=()",
    "usb=()",
    "accelerometer=()",
    "gyroscope=()",
    "magnetometer=()",
    "interest-cohort=()",
)

_CSP_RO_REQUIRED = (
    "default-src 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "script-src",
    "www.googletagmanager.com",
    "connect-src",
    "www.google-analytics.com",
    "manifest-src 'self'",
)


def _assert_security_headers(response: object) -> None:
    headers = response.headers  # type: ignore[attr-defined]
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    permissions = headers.get("Permissions-Policy") or ""
    for token in _PERMISSIONS_REQUIRED:
        assert token in permissions, token
    assert "clipboard-write=()" not in permissions
    assert "clipboard-read=()" not in permissions

    assert "Content-Security-Policy" not in headers
    csp_ro = headers.get("Content-Security-Policy-Report-Only")
    assert csp_ro is not None
    for token in _CSP_RO_REQUIRED:
        assert token in csp_ro, token


def test_security_headers_on_html_200(client: TestClient) -> None:
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    _assert_security_headers(response)


def test_security_headers_on_branded_404(client: TestClient) -> None:
    response = client.get(
        "/security-headers-missing-path",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404
    assert "페이지를 찾을 수 없습니다." in response.text
    _assert_security_headers(response)


def test_security_headers_on_branded_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("APP_BASE_URL", "http://testserver")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    get_settings.cache_clear()
    get_templates.cache_clear()
    app = create_app()

    @app.get("/__clips_security_header_boom")
    def boom() -> None:
        raise RuntimeError("security-header-boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/__clips_security_header_boom",
            headers={"Accept": "text/html"},
        )
        assert response.status_code == 500
        assert "일시적인 오류가 발생했습니다." in response.text
        _assert_security_headers(response)

    get_settings.cache_clear()
    get_templates.cache_clear()


def test_security_headers_on_static_file(client: TestClient) -> None:
    response = client.get("/static/css/base.css")
    assert response.status_code == 200
    _assert_security_headers(response)
