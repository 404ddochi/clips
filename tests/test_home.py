"""Home and SEO route tests."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient


def test_home_returns_200(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_home_contains_clips(client: TestClient) -> None:
    html = client.get("/").text
    assert "CLIPS" in html


def test_home_has_title(client: TestClient) -> None:
    html = client.get("/").text
    assert "<title>" in html
    assert "클립스" in html


def test_home_has_meta_description(client: TestClient) -> None:
    html = client.get("/").text
    assert 'meta name="description"' in html
    assert "비공식 정보 사이트" in html


def test_home_has_single_h1(client: TestClient) -> None:
    html = client.get("/").text
    h1_tags = re.findall(r"<h1[^>]*>", html, flags=re.IGNORECASE)
    assert len(h1_tags) == 1


def test_robots_txt(client: TestClient) -> None:
    response = client.get("/robots.txt")
    assert response.status_code == 200
    body = response.text
    assert "User-agent: *" in body
    assert "Sitemap: http://testserver/sitemap.xml" in body


def test_sitemap_xml(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    body = response.text
    assert "<loc>http://testserver/</loc>" in body
    assert "<lastmod>" in body


def test_not_found_page(client: TestClient) -> None:
    response = client.get("/does-not-exist", headers={"Accept": "text/html"})
    assert response.status_code == 404
    assert "찾을 수 없습니다" in response.text
