"""Unified search page and service tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from app.services.content_types import GuideEntry
from app.services.news_mock_data import list_news
from app.services.search import (
    MAX_QUERY_LENGTH,
    escape_like_wildcards,
    normalize_search_query,
    search_all,
)
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _json_ld(html: str) -> list[dict[str, object]]:
    soup = _soup(html)
    return [
        json.loads(script.string or "")
        for script in soup.find_all("script", attrs={"type": "application/ld+json"})
    ]


def test_normalize_search_query() -> None:
    assert normalize_search_query(None).should_search is False
    assert normalize_search_query("   ").should_search is False
    assert normalize_search_query("  클래스   정보 ").normalized == "클래스 정보"
    long = "가" * (MAX_QUERY_LENGTH + 1)
    bad = normalize_search_query(long)
    assert bad.should_search is False
    assert "100자" in bad.error
    assert escape_like_wildcards("100%_off") == "100\\%\\_off"


def test_search_page_idle(client: TestClient) -> None:
    response = client.get("/search")
    assert response.status_code == 200
    soup = _soup(response.text)
    assert soup.find("title").get_text() == "통합 검색 - CLIPS"
    form = soup.find("form", attrs={"role": "search"})
    assert form is not None
    assert form.find("input", attrs={"name": "q"}) is not None
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots["content"] == "noindex, follow"
    canonical = soup.find("link", rel="canonical")
    assert canonical["href"] == "http://testserver/search"
    og_url = soup.find("meta", attrs={"property": "og:url"})
    assert og_url["content"] == "http://testserver/search"
    payloads = _json_ld(response.text)
    assert {item.get("@type") for item in payloads} == {"BreadcrumbList"}
    assert "검색어를 입력해 주세요" in response.text


def test_search_blank_query(client: TestClient) -> None:
    response = client.get("/search", params={"q": "   "})
    assert response.status_code == 200
    assert "검색어를 입력해 주세요" in response.text


def test_search_title_match_and_groups(client: TestClient) -> None:
    notice = list_news(category="notice")[0]
    response = client.get("/search", params={"q": notice.title})
    assert response.status_code == 200
    soup = _soup(response.text)
    assert soup.find("title").get_text() == f"{notice.title} 검색 결과 - CLIPS"
    assert f"‘{notice.title}’ 검색 결과" in response.text
    assert notice.title in response.text
    hrefs = {a.get("href") for a in soup.find_all("a", href=True)}
    assert any(f"/news/notices/{notice.slug}" in (h or "") for h in hrefs)
    assert soup.select(".search-group")
    payloads = _json_ld(response.text)
    assert not any(item.get("@type") == "Article" for item in payloads)


def test_search_case_insensitive_and_korean(client: TestClient) -> None:
    response = client.get("/search", params={"q": "clips"})
    assert response.status_code == 200
    assert client.get("/search", params={"q": "클래스"}).status_code == 200
    html = client.get("/search", params={"q": "파이터"}).text
    assert "파이터" in html
    assert "/classes/fighter" in html


def test_search_no_results(client: TestClient) -> None:
    response = client.get("/search", params={"q": "존재하지않는검색어xyz"})
    assert response.status_code == 200
    assert "검색 결과가 없습니다" in response.text
    assert _soup(response.text).select(".search-group") == []


def test_search_type_filter(client: TestClient) -> None:
    response = client.get("/search", params={"q": "파이터", "type": "classes"})
    soup = _soup(response.text)
    labels = [el.get_text(strip=True) for el in soup.select(".search-group__label")]
    assert labels == ["클래스"]
    # Invalid type falls back to all
    assert client.get("/search", params={"q": "파이터", "type": "nope"}).status_code == 200


def test_search_security_escaping(client: TestClient) -> None:
    payload = '<script>alert(1)</script>'
    response = client.get("/search", params={"q": payload})
    assert response.status_code == 200
    # Escaped in HTML text / attributes — raw script tag must not execute from query.
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text or "alert(1)" in response.text

    for q in ("%_", "O'Reilly", '"quote"', "</script>", "SELECT * FROM users"):
        assert client.get("/search", params={"q": q}).status_code == 200


def test_search_long_query_validation(client: TestClient) -> None:
    response = client.get("/search", params={"q": "가" * (MAX_QUERY_LENGTH + 5)})
    assert response.status_code == 200
    assert "100자" in response.text
    assert client.get("/search").headers.get("content-type", "").startswith("text/html")


def test_search_canonical_strips_query(client: TestClient) -> None:
    soup = _soup(client.get("/search", params={"q": "보스", "type": "bosses"}).text)
    assert soup.find("link", rel="canonical")["href"] == "http://testserver/search"
    assert soup.find("meta", attrs={"property": "og:url"})["content"] == (
        "http://testserver/search"
    )


def test_header_search_entry(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    link = soup.select_one("a.header-search")
    assert link is not None
    assert link.get("href", "").endswith("/search")
    assert "통합 검색" in link.get("aria-label", "")


def test_home_search_action(client: TestClient) -> None:
    payloads = _json_ld(client.get("/").text)
    website = next(item for item in payloads if item.get("@type") == "WebSite")
    action = website["potentialAction"]
    assert action["@type"] == "SearchAction"
    assert action["target"]["urlTemplate"] == (
        "http://testserver/search?q={search_term_string}"
    )


def test_search_excludes_draft_guides(monkeypatch: pytest.MonkeyPatch) -> None:
    draft = GuideEntry(
        slug="draft-only",
        title="초안 전용 공략",
        summary="초안 요약",
        category="beginner",
        category_label="입문",
        author_name="CLIPS",
        published_at=datetime(2026, 7, 1, tzinfo=UTC),
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
        reading_minutes=3,
        status="draft",
    )
    published = GuideEntry(
        slug="live-guide",
        title="공개 공략",
        summary="공개 요약",
        category="beginner",
        category_label="입문",
        author_name="CLIPS",
        published_at=datetime(2026, 7, 2, tzinfo=UTC),
        updated_at=datetime(2026, 7, 2, tzinfo=UTC),
        reading_minutes=4,
        status="published",
    )
    monkeypatch.setattr(
        "app.services.guide_data.GUIDE_ENTRIES",
        (draft, published),
    )
    result = search_all("공략")
    guide_group = next(
        (group for group in result.groups if group.content_type == "guides"),
        None,
    )
    assert guide_group is not None
    urls = [item.url for item in guide_group.results]
    assert "/guides/live-guide" in urls
    assert "/guides/draft-only" not in urls


def test_search_relevance_title_beats_summary() -> None:
    # Class name "파이터" should outrank summary-only matches when both exist.
    result = search_all("파이터")
    assert result.total_count >= 1
    first = result.groups[0].results[0]
    assert first.title == "파이터"
    assert first.relevance_score >= 60


def test_search_empty_catalogues_ok() -> None:
    # Items/bosses/maps may be empty — must not error.
    result = search_all("아이템")
    assert result.error == ""
    assert isinstance(result.groups, tuple)
