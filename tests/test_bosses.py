"""Boss list / detail tests (no fabricated on-screen boss catalogue)."""

from __future__ import annotations

from app.main import app
from app.services.boss_data import BOSS_ITEMS, get_boss_by_slug, has_boss_catalogue, list_bosses
from app.services.content_types import BossItem
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

# Screen data stays empty. Fixture is test-only and never registered in BOSS_ITEMS.
_TEST_BOSS_FIXTURE = BossItem(
    slug="fixture-seal",
    name="테스트 봉인",
    name_en="Fixture Seal",
    symbol="boss-seal",
    accent="seal",
    category="테스트 분류",
    region="테스트 지역",
    summary="테스트 전용 픽스처이며 화면에 노출되지 않습니다.",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_bosses_route_endpoint() -> None:
    assert app.url_path_for("bosses") == "/bosses"
    assert app.url_path_for("boss_detail", slug="any") == "/bosses/any"


def test_boss_catalogue_is_empty_until_official() -> None:
    assert BOSS_ITEMS == ()
    assert list_bosses() == ()
    assert has_boss_catalogue() is False
    assert get_boss_by_slug("fixture-seal") is None
    assert _TEST_BOSS_FIXTURE.slug == "fixture-seal"


def test_bosses_index_waiting_ok(client: TestClient) -> None:
    response = client.get("/bosses")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert soup.find("h1") is not None
    assert "보스" in soup.find("h1").get_text()
    assert "이클립스의 공식 보스 정보를 정리합니다." in html
    assert "공식 보스 정보 대기 중" in html
    assert soup.select_one(".boss-waiting") is not None
    assert soup.select_one(".boss-card") is None
    assert "테스트 봉인" not in html
    assert "권장 전투력" not in html
    assert "드랍 아이템" in html  # muted upcoming chip label only
    assert "등장 좌표" not in html
    assert "⚔" not in html
    assert "bosses.css" in html
    assert soup.find("meta", attrs={"name": "robots"})["content"].find("noindex") != -1
    nav = soup.find("nav", attrs={"aria-label": "다른 CLIPS 메뉴"})
    assert nav is not None


def test_bosses_seo_waiting(client: TestClient) -> None:
    soup = _soup(client.get("/bosses").text)
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == "보스 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc is not None
    assert "공개되면" in desc.get("content", "")
    assert "드랍 정보" not in desc.get("content", "")


def test_boss_detail_unknown_404(client: TestClient) -> None:
    response = client.get("/bosses/not-a-real-boss")
    assert response.status_code == 404


def test_boss_nav_link(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    hrefs = {a.get("href") for a in soup.find_all("a", href=True)}
    assert any("/bosses" in (h or "") for h in hrefs)


def test_bosses_not_generic_coming_soon(client: TestClient) -> None:
    html = client.get("/bosses").text
    assert "클래스별 특징" not in html
    soup = _soup(html)
    assert soup.select_one(".coming-soon") is None
    assert "BOSSES" in html
