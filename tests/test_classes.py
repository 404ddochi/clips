"""Class list / detail page tests (publicly disclosed info only)."""

from __future__ import annotations

from app.main import app
from app.services.class_data import CLASS_ITEMS, filter_classes, parse_class_filter
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_classes_route_endpoint() -> None:
    assert app.url_path_for("classes") == "/classes"
    assert app.url_path_for("class_detail", slug="fighter") == "/classes/fighter"


def test_classes_index_ok(client: TestClient) -> None:
    response = client.get("/classes")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert "준비 중" not in soup.find("h1").get_text()
    assert len(soup.find_all("h1")) == 1
    assert "클래스" in soup.find("h1").get_text()
    assert soup.find("meta", attrs={"name": "robots"})["content"].find("noindex") != -1
    assert "classes.css" in html
    assert soup.select(".class-card")
    assert len(soup.select(".class-card")) == len(CLASS_ITEMS)
    assert "파이터" in html
    assert "레인저" in html
    assert "소서리스" in html
    assert "어쌔신" in html
    assert "⚔" not in html
    nav = soup.find("nav", attrs={"aria-label": "전투 스타일 필터"})
    assert nav is not None
    labels = [a.get_text(strip=True) for a in nav.select(".class-filters__link")]
    assert labels == ["전체", "근거리", "원거리", "마법", "지원"]


def test_classes_seo(client: TestClient) -> None:
    soup = _soup(client.get("/classes").text)
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == (
        "클래스 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
    )
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc is not None
    assert "클래스" in desc.get("content", "")


def test_classes_filter_melee(client: TestClient) -> None:
    response = client.get("/classes", params={"style": "melee"})
    assert response.status_code == 200
    soup = _soup(response.text)
    active = soup.select_one(".class-filters__link.is-active")
    assert active is not None
    assert active.get_text(strip=True) == "근거리"
    cards = soup.select(".class-card")
    names = {c.select_one(".class-card__title").get_text(strip=True) for c in cards}
    assert "파이터" in names
    assert "어쌔신" in names
    assert "레인저" not in names


def test_classes_filter_support(client: TestClient) -> None:
    response = client.get("/classes", params={"style": "support"})
    soup = _soup(response.text)
    cards = soup.select(".class-card")
    names = {c.select_one(".class-card__title").get_text(strip=True) for c in cards}
    assert names == {"소서리스"}


def test_classes_detail_ok(client: TestClient) -> None:
    response = client.get("/classes/fighter")
    assert response.status_code == 200
    soup = _soup(response.text)
    assert len(soup.find_all("h1")) == 1
    assert "파이터" in soup.find("h1").get_text()
    assert "한손검" in response.text
    assert "대검" in response.text
    assert "추후 공개 예정" in response.text
    assert "스킬" in response.text
    assert "빌드" in response.text
    assert soup.select_one(".class-hero") is not None
    assert soup.select_one(".class-info-card") is not None
    assert soup.find("h2", string="공개 정보") is None
    assert "스킬 목록과 효과" not in response.text
    assert soup.select_one(".class-related-chip") is not None


def test_classes_detail_assassin_pending_styles(client: TestClient) -> None:
    response = client.get("/classes/assassin")
    assert response.status_code == 200
    assert "카타나" in response.text
    assert "공개 예정" in response.text


def test_classes_detail_404(client: TestClient) -> None:
    response = client.get("/classes/missing", headers={"Accept": "text/html"})
    assert response.status_code == 404


def test_classes_helpers() -> None:
    assert parse_class_filter(None) == "all"
    assert parse_class_filter("magic") == "magic"
    assert parse_class_filter("nope") == "all"
    assert len(filter_classes(style="ranged")) == 1


def test_classes_css(client: TestClient) -> None:
    assert client.get("/static/css/pages/classes.css").status_code == 200
