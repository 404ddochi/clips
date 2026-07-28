"""Guides list / detail tests (no fabricated on-screen guide catalogue)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.main import app
from app.services import guide_data
from app.services.content_types import GuideEntry, GuideSection, GuideSourceLink
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

_PUBLISHED = GuideEntry(
    slug="fixture-intro",
    title="테스트 입문 가이드",
    summary="테스트 전용 published 픽스처입니다.",
    category="beginner",
    category_label="입문",
    author_name="CLIPS Desk",
    published_at=datetime(2026, 7, 1, tzinfo=UTC),
    updated_at=datetime(2026, 7, 20, tzinfo=UTC),
    reading_minutes=4,
    sections=(
        GuideSection(
            heading="시작하기",
            body="본문 검색어 growth-body를 포함합니다.",
            bullets=("첫 단계",),
            tip="천천히 확인하세요.",
        ),
        GuideSection(
            heading="다음 단계",
            body="두 번째 섹션입니다.",
            warning="미확인 정보는 따르지 마세요.",
        ),
    ),
    tags=("입문", "성장"),
    source_links=(
        GuideSourceLink(
            label="이클립스 공식 홈",
            url="https://eclipse.onstove.com/ko/home",
            source_type="official_home",
            checked_at=datetime(2026, 7, 18, tzinfo=UTC),
        ),
    ),
    is_featured=True,
    status="published",
)

_DRAFT = GuideEntry(
    slug="fixture-draft",
    title="초보자 필수 공략",
    summary="draft는 화면에 노출되면 안 됩니다.",
    category="beginner",
    category_label="입문",
    author_name="Hidden",
    published_at=datetime(2026, 7, 1, tzinfo=UTC),
    updated_at=datetime(2026, 7, 2, tzinfo=UTC),
    reading_minutes=2,
    sections=(GuideSection(heading="숨김", body="draft body"),),
    status="draft",
)

_PUBLISHED_B = GuideEntry(
    slug="fixture-system",
    title="시스템 안내 샘플",
    summary="관련 공략 테스트용 두 번째 published.",
    category="system",
    category_label="시스템",
    author_name="CLIPS Desk",
    published_at=datetime(2026, 6, 1, tzinfo=UTC),
    updated_at=datetime(2026, 7, 10, tzinfo=UTC),
    reading_minutes=3,
    sections=(GuideSection(heading="개요", body="시스템 요약"),),
    tags=("시스템",),
    status="published",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_guides_route_endpoint() -> None:
    assert app.url_path_for("guides") == "/guides"
    assert app.url_path_for("guide_detail", slug="any") == "/guides/any"


def test_guide_catalogue_is_empty_until_authored() -> None:
    assert guide_data.GUIDE_ENTRIES == ()
    assert guide_data.list_published_guides() == ()
    assert guide_data.has_guide_catalogue() is False
    assert guide_data.get_guide_by_slug("fixture-intro") is None


def test_guides_index_desk_waiting_ok(client: TestClient) -> None:
    response = client.get("/guides")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert soup.find("h1") is not None
    assert "공략" in soup.find("h1").get_text()
    assert "CLIPS가 직접 정리한 가이드와 공략을 준비합니다." in html
    assert "CLIPS 공략을 준비하고 있습니다." in html
    assert soup.select_one(".guide-desk") is not None
    assert soup.select_one(".guide-card") is None
    assert soup.select_one(".guide-search") is None
    assert soup.select_one(".guide-filters") is None
    assert "초보자 필수 공략" not in html
    assert "가장 빠른 육성법" not in html
    assert "티어표" not in html
    assert "추천 직업" not in html
    assert "guides.css" in html
    assert soup.find("meta", attrs={"name": "robots"})["content"] == "index, follow"
    chips = [
        chip.get_text(strip=True)
        for chip in soup.select(".guide-desk__topics .guide-prep-chip")
    ]
    assert chips == ["입문", "성장", "클래스", "콘텐츠", "시스템", "탐험"]


def test_guides_seo_waiting(client: TestClient) -> None:
    soup = _soup(client.get("/guides").text)
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == "공략 - CLIPS"
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc is not None
    assert "비공식 공략" in desc.get("content", "")
    assert "필수 공략" not in desc.get("content", "")


def test_guide_detail_unknown_404(client: TestClient) -> None:
    assert client.get("/guides/not-a-real-guide").status_code == 404


def test_guides_nav_link(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    hrefs = {a.get("href") for a in soup.find_all("a", href=True)}
    assert any("/guides" in (h or "") for h in hrefs)


def test_guides_not_generic_coming_soon(client: TestClient) -> None:
    html = client.get("/guides").text
    soup = _soup(html)
    assert soup.select_one(".coming-soon") is None
    assert "GUIDES" in html
    assert "준비 중" not in soup.find("h1").get_text()


def test_draft_not_listed_or_detail(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(guide_data, "GUIDE_ENTRIES", (_DRAFT,))
    html = client.get("/guides").text
    assert "초보자 필수 공략" not in html
    assert client.get("/guides/fixture-draft").status_code == 404


def test_published_list_and_detail(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(guide_data, "GUIDE_ENTRIES", (_PUBLISHED, _DRAFT))
    response = client.get("/guides")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert soup.select_one(".guide-desk") is None
    assert "테스트 입문 가이드" in html
    assert "초보자 필수 공략" not in html
    assert soup.select_one(".guide-search") is not None
    assert "공략 1개" in html

    detail = client.get("/guides/fixture-intro")
    assert detail.status_code == 200
    detail_html = detail.text
    assert "비공식 가이드" in detail_html
    assert "CLIPS Desk" in detail_html
    assert "2026-07-01" in detail_html
    assert "2026-07-20" in detail_html
    assert "이클립스 공식 홈" in detail_html
    assert "목차" in detail_html
    assert "시작하기" in detail_html
    assert "검증 완료" not in detail_html


def test_guide_ssr_search_and_category(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(guide_data, "GUIDE_ENTRIES", (_PUBLISHED, _PUBLISHED_B, _DRAFT))
    soup = _soup(client.get("/guides").text)
    labels = [a.get_text(strip=True) for a in soup.select(".guide-filters__link")]
    assert labels[0] == "전체"
    assert "입문" in labels
    assert "시스템" in labels

    by_cat = client.get("/guides?category=beginner")
    assert "테스트 입문 가이드" in by_cat.text
    assert "시스템 안내 샘플" not in by_cat.text

    by_q = client.get("/guides?q=growth-body")
    assert "테스트 입문 가이드" in by_q.text
    assert "시스템 안내 샘플" not in by_q.text

    combo = client.get("/guides?q=성장&category=beginner")
    assert combo.status_code == 200
    assert "테스트 입문 가이드" in combo.text

    empty = client.get("/guides?q=존재하지않는검색어xyz")
    assert "조건에 맞는 공략이 없습니다." in empty.text


def test_related_guides_when_multiple(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(guide_data, "GUIDE_ENTRIES", (_PUBLISHED, _PUBLISHED_B))
    html = client.get("/guides/fixture-intro").text
    assert "관련 공략" in html
    assert "시스템 안내 샘플" in html
