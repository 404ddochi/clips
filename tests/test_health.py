"""Health endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


def test_health_status_ok(client: TestClient) -> None:
    payload = client.get("/health").json()
    assert payload["status"] == "ok"


def test_health_service_name(client: TestClient) -> None:
    payload = client.get("/health").json()
    assert payload["service"] == "CLIPS"


def test_health_hides_environment_and_internals(client: TestClient) -> None:
    response = client.get("/health")
    payload = response.json()
    assert "environment" not in payload
    assert "version" not in payload
    assert set(payload.keys()) == {"status", "service"}
    body = response.text
    assert "clips.db" not in body
    assert "/var/www" not in body
    assert "SECRET" not in body
    assert "Traceback" not in body


def test_health_cache_and_robots_headers(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_health_db_failure_returns_503_without_details(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "SECRET_DB_PATH_/var/www/clips/clips.db"

    def boom_session() -> object:
        raise RuntimeError(secret)

    monkeypatch.setattr("app.routers.health.SessionLocal", boom_session)
    response = client.get("/health")
    assert response.status_code == 503
    payload = response.json()
    assert payload == {"status": "degraded", "service": "CLIPS"}
    assert secret not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"
