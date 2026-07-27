"""Health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_ok(client: TestClient) -> None:
    payload = client.get("/health").json()
    assert payload["status"] == "ok"


def test_health_service_name(client: TestClient) -> None:
    payload = client.get("/health").json()
    assert payload["service"] == "CLIPS"
