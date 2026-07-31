"""Production OpenAPI surface blocking uses branded 404."""

from __future__ import annotations

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from starlette.responses import Response


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _assert_branded_404(response: Response) -> None:
    assert response.status_code == 404
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    soup = _soup(html)
    assert "페이지를 찾을 수 없습니다." in html
    assert soup.select_one(".not-found-hero") is not None
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    content = robots.get("content") or ""
    assert "noindex" in content
    assert "nofollow" in content
    assert soup.find("link", attrs={"rel": "canonical"}) is None
    assert not soup.find_all("script", attrs={"type": "application/ld+json"})


def test_production_docs_html_is_branded_404(production_client: TestClient) -> None:
    _assert_branded_404(
        production_client.get("/docs", headers={"Accept": "text/html"}),
    )


def test_production_redoc_html_is_branded_404(production_client: TestClient) -> None:
    _assert_branded_404(
        production_client.get("/redoc", headers={"Accept": "text/html"}),
    )


def test_production_openapi_json_is_plain_404(production_client: TestClient) -> None:
    response = production_client.get(
        "/openapi.json",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 404
    assert response.text == "Not Found"


def test_local_docs_still_available(local_client: TestClient) -> None:
    docs = local_client.get("/docs", headers={"Accept": "text/html"})
    assert docs.status_code == 200
    openapi = local_client.get("/openapi.json", headers={"Accept": "application/json"})
    assert openapi.status_code == 200
    payload = openapi.json()
    assert isinstance(payload, dict)
    assert "openapi" in payload
