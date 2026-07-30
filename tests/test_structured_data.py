"""JSON-LD structured data tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.config import Settings, get_settings
from app.core.constants import DEFAULT_HOME_DESCRIPTION, DEFAULT_HOME_TITLE
from app.services.content_types import ArticleBlock, GuideEntry, NewsItem
from app.services.news_mock_data import list_news
from app.services.structured_data import (
    build_guide_article_schema,
    build_home_structured_data,
    build_news_article_schema,
    build_organization_schema,
    build_website_schema,
    clean_structured_text,
    collect_json_ld_items,
    format_schema_date,
    organization_id,
)
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _json_ld_payloads(html: str) -> list[dict[str, object]]:
    soup = _soup(html)
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    return [json.loads(script.string or "") for script in scripts]


def _by_type(payloads: list[dict[str, object]], type_name: str) -> dict[str, object]:
    return next(item for item in payloads if item.get("@type") == type_name)


def test_clean_structured_text() -> None:
    assert clean_structured_text("  <b>안녕</b> &amp; 세상  ") == "안녕 & 세상"
    assert clean_structured_text("   ") is None
    assert clean_structured_text(None) is None


def test_format_schema_date_timezone() -> None:
    value = datetime(2026, 7, 28, 1, 30, tzinfo=UTC)
    assert format_schema_date(value, timezone="Asia/Seoul") == (
        "2026-07-28T10:30:00+09:00"
    )


def test_home_website_and_organization_builders() -> None:
    settings = Settings(SITE_URL="https://clips.example.com")
    website = build_website_schema(settings)
    organization = build_organization_schema(settings)
    assert website["@type"] == "WebSite"
    assert website["@id"] == "https://clips.example.com/#website"
    assert website["url"] == "https://clips.example.com/"
    assert website["name"] == "CLIPS"
    assert website["alternateName"] == DEFAULT_HOME_TITLE
    assert website["description"] == DEFAULT_HOME_DESCRIPTION
    assert website["inLanguage"] == "ko-KR"
    assert website["publisher"] == {"@id": organization_id(settings)}
    action = website["potentialAction"]
    assert action["@type"] == "SearchAction"
    assert action["target"]["urlTemplate"] == (
        "https://clips.example.com/search?q={search_term_string}"
    )
    assert action["query-input"] == "required name=search_term_string"
    assert "sameAs" not in organization
    assert organization["logo"] == (
        "https://clips.example.com/static/icons/android-chrome-512x512.png"
    )
    assert organization["description"].startswith("이클립스")


def test_home_page_json_ld(client: TestClient) -> None:
    payloads = _json_ld_payloads(client.get("/").text)
    types = [item.get("@type") for item in payloads]
    assert types.count("WebSite") == 1
    assert types.count("Organization") == 1
    assert "BreadcrumbList" not in types
    assert "Article" not in types
    website = _by_type(payloads, "WebSite")
    organization = _by_type(payloads, "Organization")
    assert website["name"] == "CLIPS"
    assert website["url"] == "http://testserver/"
    assert website["alternateName"] == DEFAULT_HOME_TITLE
    assert website["publisher"]["@id"] == organization["@id"]
    action = website["potentialAction"]
    assert action["@type"] == "SearchAction"
    assert "{search_term_string}" in action["target"]["urlTemplate"]
    assert "/search?q=" in action["target"]["urlTemplate"]
    assert "sameAs" not in organization
    assert organization["logo"].endswith("/static/icons/android-chrome-512x512.png")


def test_public_list_breadcrumb_only(client: TestClient) -> None:
    for path in (
        "/news",
        "/news/notices",
        "/news/events",
        "/news/patch-notes",
        "/classes",
        "/contents",
        "/items",
        "/bosses",
        "/maps",
        "/guides",
        "/coupons",
    ):
        payloads = _json_ld_payloads(client.get(path).text)
        assert len(payloads) == 1, path
        crumb = payloads[0]
        assert crumb["@type"] == "BreadcrumbList", path
        items = crumb["itemListElement"]
        assert len(items) >= 2, path
        positions = [entry["position"] for entry in items]
        assert positions == list(range(1, len(items) + 1)), path
        assert items[0]["name"] == "홈"
        assert items[0]["item"] == "http://testserver/"
        assert items[-1]["item"] == f"http://testserver{path}"
        assert all(entry.get("name") for entry in items)
        assert not any(item.get("@type") == "Article" for item in payloads)


def test_news_detail_article_and_breadcrumb(client: TestClient) -> None:
    notice = list_news(category="notice")[0]
    path = f"/news/notices/{notice.slug}"
    payloads = _json_ld_payloads(client.get(path).text)
    types = {item.get("@type") for item in payloads}
    assert types == {"BreadcrumbList", "Article"}
    article = _by_type(payloads, "Article")
    assert article["headline"] == notice.title
    assert article["url"] == f"http://testserver{path}"
    assert article["mainEntityOfPage"]["@id"] == f"http://testserver{path}"
    assert article["@id"] == f"http://testserver{path}#article"
    assert article["datePublished"].startswith("2026-")
    assert article["publisher"]["@id"] == "http://testserver/#organization"
    assert article["articleSection"] == "공지"
    assert "image" not in article
    crumb = _by_type(payloads, "BreadcrumbList")
    names = [entry["name"] for entry in crumb["itemListElement"]]
    assert names == ["홈", "소식", "공지", notice.title]


def test_class_detail_has_breadcrumb_without_article(client: TestClient) -> None:
    payloads = _json_ld_payloads(client.get("/classes/fighter").text)
    assert {item.get("@type") for item in payloads} == {"BreadcrumbList"}
    crumb = payloads[0]
    names = [entry["name"] for entry in crumb["itemListElement"]]
    assert names == ["홈", "클래스", "파이터"]


def test_guide_article_builder_published_only() -> None:
    settings = Settings(SITE_URL="https://clips.example.com")
    published = GuideEntry(
        slug="sample-guide",
        title='초보 가이드 <b>테스트</b> "인용"',
        summary="요약입니다.",
        category="beginner",
        category_label="입문",
        author_name="CLIPS Editor",
        published_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        reading_minutes=5,
        tags=("입문",),
        status="published",
    )
    draft = GuideEntry(
        slug="draft-guide",
        title="초안",
        summary="초안 요약",
        category="beginner",
        category_label="입문",
        author_name="CLIPS",
        published_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        reading_minutes=3,
        status="draft",
    )
    article = build_guide_article_schema(
        settings,
        guide=published,
        page_url="/guides/sample-guide",
        description="요약입니다.",
    )
    assert article is not None
    assert article["headline"] == '초보 가이드 테스트 "인용"'
    assert article["author"] == {"@type": "Person", "name": "CLIPS Editor"}
    assert article["articleSection"] == "입문"
    assert "image" not in article
    assert build_guide_article_schema(
        settings,
        guide=draft,
        page_url="/guides/draft-guide",
        description="초안 요약",
    ) is None


def test_news_article_description_matches_seo() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    item = NewsItem(
        slug="sample",
        category="event",
        title="이벤트",
        summary="<p>요약   텍스트</p>",
        published_at=datetime(2026, 7, 20, 10, 0, tzinfo=UTC),
        updated_at=None,
        source_name="CLIPS Mock",
        source_url=None,
        is_featured=False,
        status_label="샘플",
        body=(ArticleBlock(kind="paragraph", text="본문"),),
        badge_label="이벤트",
        badge_variant="event",
    )
    description = "요약 텍스트"
    article = build_news_article_schema(
        settings,
        item=item,
        page_url="/news/events/sample",
        description=description,
    )
    assert article is not None
    assert article["description"] == description
    assert article["articleSection"] == "이벤트"


def test_json_ld_script_escape_and_parse(client: TestClient) -> None:
    # Home payloads must remain parseable JSON even with Korean text.
    html = client.get("/").text
    for payload in _json_ld_payloads(html):
        assert payload["@context"] == "https://schema.org"
        dumped = json.dumps(payload, ensure_ascii=False)
        assert "</script>" not in dumped.lower()


def test_structured_data_escapes_script_breakout() -> None:
    items = collect_json_ld_items(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "break </script><script>alert(1)</script>",
        }
    )
    from app.dependencies import _json_script

    rendered = str(_json_script(items[0]))
    assert "<script>" not in rendered
    assert "\\u003c" in rendered
    parsed = json.loads(rendered)
    assert parsed["headline"].startswith("break")
    assert "</script>" in parsed["headline"]


def test_404_and_dev_have_no_json_ld(
    client: TestClient,
    local_client: TestClient,
) -> None:
    assert _json_ld_payloads(
        client.get("/missing-json-ld", headers={"Accept": "text/html"}).text
    ) == []
    assert _json_ld_payloads(local_client.get("/dev/design-system").text) == []


def test_home_structured_data_helper() -> None:
    settings = Settings(SITE_URL="https://clips.example.com/")
    items = build_home_structured_data(settings)
    assert len(items) == 2
    assert {item["@type"] for item in items} == {"WebSite", "Organization"}
