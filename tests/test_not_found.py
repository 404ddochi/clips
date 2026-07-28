"""Branded 404 page tests."""

from __future__ import annotations

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/this-route-does-not-exist", headers={"Accept": "text/html"})
    assert response.status_code == 404


def test_not_found_branded_page(client: TestClient) -> None:
    response = client.get("/missing-clips-page", headers={"Accept": "text/html"})
    assert response.status_code == 404
    html = response.text
    soup = _soup(html)

    title = soup.find("title")
    assert title is not None
    assert "페이지를 찾을 수 없습니다" in title.get_text()
    assert "CLIPS" in title.get_text()

    h1 = soup.find("h1")
    assert h1 is not None
    assert h1.get_text(strip=True) == "페이지를 찾을 수 없습니다."
    assert "입력한 주소가 변경되었거나" in html
    assert "아래 메뉴에서 다시 찾아보세요" in html
    assert soup.select_one(".not-found-hero") is not None
    assert soup.select_one(".icon--compass-sigil") is not None
    assert "not_found.css" in html
    assert "비공식 정보 플랫폼" in html


def test_not_found_shortcuts(client: TestClient) -> None:
    soup = _soup(client.get("/nope", headers={"Accept": "text/html"}).text)
    nav = soup.find("nav", attrs={"aria-label": "주요 메뉴 바로가기"})
    assert nav is not None
    labels = [a.get_text(strip=True) for a in nav.select(".not-found-links__button")]
    assert labels == ["홈", "소식", "클래스", "아이템", "보스", "지도", "공략", "쿠폰"]


def test_not_found_seo_noindex_without_canonical(client: TestClient) -> None:
    soup = _soup(client.get("/ghost", headers={"Accept": "text/html"}).text)
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert "noindex" in robots.get("content", "")
    assert soup.find("link", attrs={"rel": "canonical"}) is None
    assert soup.find("meta", attrs={"property": "og:url"}) is None


def test_not_found_plain_response_without_html_accept(client: TestClient) -> None:
    response = client.get("/ghost-plain", headers={"Accept": "application/json"})
    assert response.status_code == 404
    assert response.text == "Not Found"
