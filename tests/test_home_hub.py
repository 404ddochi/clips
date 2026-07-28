"""Home hub upgrade tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from app.services.content_types import GuideEntry
from app.services.home_page_data import (
    COUPON_LIMIT,
    GUIDE_LIMIT,
    NEWS_LIMIT,
    PATCH_LIMIT,
    build_active_coupons,
    build_home_page_data,
    build_latest_guides,
    build_latest_news,
    build_latest_patch_notes,
)
from app.services.news_mock_data import list_news
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _json_ld(html: str) -> list[dict[str, object]]:
    return [
        json.loads(script.string or "")
        for script in _soup(html).find_all(
            "script",
            attrs={"type": "application/ld+json"},
        )
    ]


def test_home_hub_coupons_guides_full_width_not_paired_grid(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    feed_grid = soup.select_one(".home-feed-grid")
    assert feed_grid is not None
    coupon_section = soup.find(id="active-coupons-heading").find_parent("section")
    guide_section = soup.find(id="latest-guides-heading").find_parent("section")
    assert coupon_section is not None
    assert guide_section is not None
    assert "home-section--full" in coupon_section.get("class", [])
    assert "home-section--full" in guide_section.get("class", [])
    assert coupon_section.find_parent(class_="home-feed-grid") is None
    assert guide_section.find_parent(class_="home-feed-grid") is None
    assert soup.select_one(".home-feed--coupons") is not None
    assert soup.select_one(".home-feed--guides") is not None
    assert soup.select_one(".home-feed__item--empty") is not None
    assert soup.select_one(".home-empty--guides") is not None


def test_home_hub_search_form(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    form = soup.select_one("form.home-search__form")
    assert form is not None
    assert form.get("action", "").endswith("/search")
    assert form.get("role") == "search"
    assert form.find("input", attrs={"name": "q", "type": "search"}) is not None
    assert soup.select_one("a.header-search") is not None


def test_home_hub_menu_links(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    cards = soup.select(".home-menu-card")
    assert len(cards) == 6
    hrefs = [a.get("href") for a in cards]
    labels = [a.select_one(".home-menu-card__title").get_text(strip=True) for a in cards]
    assert labels == ["클래스", "콘텐츠", "아이템", "보스", "지도", "공략"]
    for needle in ("/classes", "/contents", "/items", "/bosses", "/maps", "/guides"):
        assert any(needle in (h or "") for h in hrefs)
    assert len(hrefs) == len(set(hrefs))
    assert not any("/coupons" in (h or "") for h in hrefs)
    assert not any("/news" in (h or "") for h in hrefs)


def test_home_hub_news_excludes_patch(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    section = soup.find(id="latest-news-heading").find_parent("section")
    assert section is not None
    badges = {el.get_text(strip=True) for el in section.select(".badge")}
    assert "업데이트" not in badges
    assert "패치노트" not in badges
    news = build_latest_news()
    assert len(news) <= NEWS_LIMIT
    assert all(item.badge in {"공지", "이벤트"} for item in news)
    if len(news) >= 2:
        assert news[0].published_at >= news[1].published_at


def test_home_hub_patch_notes(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    assert soup.find(id="latest-patch-heading") is not None
    patches = build_latest_patch_notes()
    assert len(patches) <= PATCH_LIMIT
    if patches:
        assert "/news/patch-notes/" in patches[0].url_path
        section = soup.find(id="latest-patch-heading").find_parent("section")
        assert patches[0].title in section.get_text()


def test_home_hub_coupons_exclude_expired(client: TestClient) -> None:
    coupons = build_active_coupons()
    assert len(coupons) <= COUPON_LIMIT
    assert all(item.status_label != "종료" for item in coupons)
    codes = {item.code for item in coupons}
    assert "CLIPS-ENDED" not in codes
    soup = _soup(client.get("/").text)
    section = soup.find(id="active-coupons-heading").find_parent("section")
    text = section.get_text()
    assert "CLIPS-ENDED" not in text
    for item in coupons:
        assert item.code in text


def test_home_hub_guides_empty_state(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    section = soup.find(id="latest-guides-heading").find_parent("section")
    assert "아직 등록된 공략이 없습니다" in section.get_text()
    assert build_latest_guides() == ()


def test_home_hub_guides_published_only(monkeypatch: pytest.MonkeyPatch) -> None:
    draft = GuideEntry(
        slug="draft-home",
        title="초안 공략",
        summary="초안",
        category="beginner",
        category_label="입문",
        author_name="CLIPS",
        published_at=datetime(2026, 7, 3, tzinfo=UTC),
        updated_at=datetime(2026, 7, 3, tzinfo=UTC),
        reading_minutes=2,
        status="draft",
    )
    published = GuideEntry(
        slug="live-home",
        title="공개 홈 공략",
        summary="공개 요약",
        category="beginner",
        category_label="입문",
        author_name="CLIPS Editor",
        published_at=datetime(2026, 7, 4, tzinfo=UTC),
        updated_at=datetime(2026, 7, 4, tzinfo=UTC),
        reading_minutes=4,
        status="published",
    )
    monkeypatch.setattr(
        "app.services.guide_data.GUIDE_ENTRIES",
        (draft, published),
    )
    guides = build_latest_guides()
    assert len(guides) == 1
    assert guides[0].slug == "live-home"
    assert len(guides) <= GUIDE_LIMIT


def test_home_hub_seo_preserved(client: TestClient) -> None:
    html = client.get("/").text
    soup = _soup(html)
    assert soup.find("title").get_text() == (
        "CLIPS - 이클립스: 더 어웨이크닝 정보 플랫폼"
    )
    assert soup.find("link", rel="canonical")["href"] == "http://testserver/"
    payloads = _json_ld(html)
    types = {item.get("@type") for item in payloads}
    assert types == {"WebSite", "Organization"}
    website = next(item for item in payloads if item["@type"] == "WebSite")
    assert website["potentialAction"]["@type"] == "SearchAction"
    assert not any(item.get("@type") == "Article" for item in payloads)


def test_home_hub_accessibility(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    assert len(soup.find_all("h1")) == 1
    for heading_id in (
        "home-menu-heading",
        "latest-news-heading",
        "latest-patch-heading",
        "active-coupons-heading",
        "latest-guides-heading",
    ):
        assert soup.find("h2", id=heading_id) is not None
    assert soup.find("label", attrs={"for": "home-search-q"}) is not None
    assert soup.select("time[datetime]")
    for icon in soup.select(".home-menu-card__icon .icon, .home-search__icon .icon"):
        parent = icon.find_parent(attrs={"aria-hidden": True})
        assert parent is not None


def test_home_page_data_builder() -> None:
    data = build_home_page_data()
    assert len(data.menu_links) == 6
    assert len(data.latest_news) <= NEWS_LIMIT
    assert len(data.latest_patch_notes) <= PATCH_LIMIT
    assert len(data.active_coupons) <= COUPON_LIMIT
    # News section must not include patch category items from list_news
    notice_event_slugs = {
        item.slug for item in list_news() if item.category in {"notice", "event"}
    }
    assert {item.slug for item in data.latest_news}.issubset(notice_event_slugs)
