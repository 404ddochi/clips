"""Item list / detail tests (no fabricated on-screen item catalogue)."""

from __future__ import annotations

from app.main import app
from app.services.content_types import ItemEntry
from app.services.item_data import (
    ITEM_ENTRIES,
    filter_items,
    get_item_by_slug,
    has_item_catalogue,
    list_items,
)
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

_TEST_ITEM_FIXTURE = ItemEntry(
    slug="fixture-sigil",
    name="테스트 코어",
    name_en="Fixture Core",
    symbol="item-sigil",
    accent="sigil",
    category="테스트 분류",
    slot_or_purpose="테스트 부위",
    summary="테스트 전용 픽스처이며 화면에 노출되지 않습니다.",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_items_route_endpoint() -> None:
    assert app.url_path_for("items") == "/items"
    assert app.url_path_for("item_detail", slug="any") == "/items/any"


def test_item_catalogue_is_empty_until_official() -> None:
    assert ITEM_ENTRIES == ()
    assert list_items() == ()
    assert has_item_catalogue() is False
    assert get_item_by_slug("fixture-sigil") is None
    assert filter_items(query="test") == ()
    assert _TEST_ITEM_FIXTURE.slug == "fixture-sigil"


def test_items_index_waiting_ok(client: TestClient) -> None:
    response = client.get("/items")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert soup.find("h1") is not None
    assert "아이템" in soup.find("h1").get_text()
    assert "공식 아이템 정보를 정리합니다." in html
    assert "공식 아이템 정보 대기 중" in html
    assert soup.select_one(".item-waiting") is not None
    assert soup.select_one(".item-card") is None
    assert soup.select_one(".item-search") is None
    assert "테스트 코어" not in html
    assert "희귀도" not in html
    assert "공격력" not in html
    assert "제작식" not in html
    assert "등급" in html  # upcoming chip only
    assert "items.css" in html
    assert soup.find("meta", attrs={"name": "robots"})["content"] == "index, follow"
    nav = soup.find("nav", attrs={"aria-label": "다른 CLIPS 메뉴"})
    assert nav is not None


def test_items_seo_waiting(client: TestClient) -> None:
    soup = _soup(client.get("/items").text)
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == "아이템 - CLIPS"
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc is not None
    assert "아이템" in desc.get("content", "")
    assert "레전드리" not in desc.get("content", "")


def test_item_detail_unknown_404(client: TestClient) -> None:
    response = client.get("/items/not-a-real-item")
    assert response.status_code == 404


def test_item_nav_link(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    hrefs = {a.get("href") for a in soup.find_all("a", href=True)}
    assert any("/items" in (h or "") for h in hrefs)


def test_items_not_generic_coming_soon(client: TestClient) -> None:
    html = client.get("/items").text
    assert "장비, 재료, 제작 정보" not in html
    soup = _soup(html)
    assert soup.select_one(".coming-soon") is None
    assert "ITEMS" in html
