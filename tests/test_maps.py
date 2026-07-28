"""Map hub list / detail tests (no fabricated on-screen region catalogue)."""

from __future__ import annotations

from app.main import app
from app.services.content_types import RegionEntry
from app.services.map_data import (
    REGION_ENTRIES,
    get_region_by_slug,
    has_region_catalogue,
    list_regions,
)
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

_TEST_REGION_FIXTURE = RegionEntry(
    slug="fixture-field",
    name="테스트 필드",
    name_en="Fixture Field",
    symbol="map-sigil",
    accent="field",
    region_kind="테스트 유형",
    world_label="테스트 월드",
    summary="테스트 전용 픽스처이며 화면에 노출되지 않습니다.",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_maps_route_endpoint() -> None:
    assert app.url_path_for("maps") == "/maps"
    assert app.url_path_for("map_detail", slug="any") == "/maps/any"


def test_region_catalogue_is_empty_until_official() -> None:
    assert REGION_ENTRIES == ()
    assert list_regions() == ()
    assert has_region_catalogue() is False
    assert get_region_by_slug("fixture-field") is None
    assert _TEST_REGION_FIXTURE.slug == "fixture-field"


def test_maps_index_waiting_ok(client: TestClient) -> None:
    response = client.get("/maps")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert soup.find("h1") is not None
    assert "지도" in soup.find("h1").get_text()
    assert "공식 지역 정보를 정리합니다." in html
    assert "공개 지역 정보 대기 중" in html
    assert soup.select_one(".map-waiting") is not None
    assert soup.select_one(".map-card") is None
    assert "테스트 필드" not in html
    assert "공식 홈페이지에 공개되는 지역 정보를 CLIPS에 순차적으로 반영합니다." in html
    assert "월드맵" in html
    assert "사냥터" in html
    chips = [
        chip.get_text(strip=True)
        for chip in soup.select(".map-waiting__topics .map-upcoming-chip")
    ]
    assert chips == ["지역", "월드맵", "사냥터", "던전", "NPC", "성소"]
    assert "maps.css" in html
    assert soup.find("meta", attrs={"name": "robots"})["content"] == "index, follow"
    nav = soup.find("nav", attrs={"aria-label": "다른 CLIPS 메뉴"})
    assert nav is not None


def test_maps_seo_waiting(client: TestClient) -> None:
    soup = _soup(client.get("/maps").text)
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == "지도 - CLIPS"
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc is not None
    assert "지역" in desc.get("content", "") or "지도" in desc.get("content", "")
    assert "월드맵" in desc.get("content", "")


def test_map_detail_unknown_404(client: TestClient) -> None:
    response = client.get("/maps/not-a-real-region")
    assert response.status_code == 404


def test_maps_nav_link(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    hrefs = {a.get("href") for a in soup.find_all("a", href=True)}
    assert any("/maps" in (h or "") for h in hrefs)


def test_maps_not_generic_coming_soon(client: TestClient) -> None:
    html = client.get("/maps").text
    soup = _soup(html)
    assert soup.select_one(".coming-soon") is None
    assert "MAP" in html
    assert "준비 중" not in soup.find("h1").get_text()
