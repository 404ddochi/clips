"""JSON-LD structured data builders (schema.org).

Returns plain dicts only. HTML serialization happens in the template via
the Jinja ``tojson`` filter (see ``app.dependencies``).
"""

from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.constants import (
    DEFAULT_HOME_DESCRIPTION,
    DEFAULT_HOME_TITLE,
    SERVICE_NAME,
    SERVICE_NAME_KO,
)
from app.services.content_types import GuideEntry, NewsCategory, NewsItem

logger = logging.getLogger(__name__)

SCHEMA_CONTEXT = "https://schema.org"
ORG_DESCRIPTION = "이클립스: 더 어웨이크닝의 비공식 정보 플랫폼입니다."

_ARTICLE_SECTION: dict[NewsCategory, str] = {
    "notice": "공지",
    "event": "이벤트",
    "patch": "패치노트",
}

_WHITESPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")


def clean_structured_text(value: str | None) -> str | None:
    """Strip HTML/entities/whitespace for JSON-LD text fields."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    cleaned = _TAG_RE.sub(" ", raw)
    cleaned = html.unescape(cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned or None


def prune_empty(value: Any) -> Any:
    """Drop None / empty strings / empty collections from nested structures."""
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            pruned = prune_empty(item)
            if pruned is None:
                continue
            if pruned == "" or pruned == [] or pruned == {}:
                continue
            out[key] = pruned
        return out or None
    if isinstance(value, (list, tuple)):
        items = [prune_empty(item) for item in value]
        items = [item for item in items if item is not None and item != "" and item != {}]
        return items or None
    return value


def organization_id(settings: Settings) -> str:
    return f"{settings.site_url}/#organization"


def website_id(settings: Settings) -> str:
    return f"{settings.site_url}/#website"


def _to_aware(value: datetime | date, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tz)
        return value.astimezone(tz)
    return datetime.combine(value, datetime.min.time(), tzinfo=tz)


def format_schema_date(
    value: datetime | date | None,
    *,
    timezone: str = "Asia/Seoul",
) -> str | None:
    """ISO 8601 date or datetime in the project timezone when possible."""
    if value is None:
        return None
    if type(value) is date:
        return value.isoformat()
    localized = _to_aware(value, timezone)
    return localized.isoformat()


def clips_organization_ref(settings: Settings) -> dict[str, str]:
    return {"@id": organization_id(settings)}


def clips_organization_author(settings: Settings) -> dict[str, str]:
    return {
        "@type": "Organization",
        "@id": organization_id(settings),
        "name": SERVICE_NAME,
    }


def build_organization_schema(settings: Settings) -> dict[str, Any]:
    """Home Organization — unofficial info platform; no invented sameAs/contact."""
    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "Organization",
        "@id": organization_id(settings),
        "name": SERVICE_NAME,
        "alternateName": SERVICE_NAME_KO,
        "url": settings.canonical_url("/"),
        "description": ORG_DESCRIPTION,
        "logo": settings.absolute_url("/static/icons/android-chrome-512x512.png"),
    }


def build_website_schema(settings: Settings) -> dict[str, Any]:
    """Home WebSite including SearchAction for `/search?q=` (real search route)."""
    search_template = f"{settings.site_url}/search?q={{search_term_string}}"
    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "WebSite",
        "@id": website_id(settings),
        "url": settings.canonical_url("/"),
        "name": SERVICE_NAME,
        "alternateName": DEFAULT_HOME_TITLE,
        "description": DEFAULT_HOME_DESCRIPTION,
        "inLanguage": "ko-KR",
        "publisher": clips_organization_ref(settings),
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": search_template,
            },
            "query-input": "required name=search_term_string",
        },
    }


def build_breadcrumb_schema(
    settings: Settings,
    crumbs: list[tuple[str, str]],
    *,
    page_url: str | None = None,
) -> dict[str, Any] | None:
    """crumbs: list of (name, absolute_or_path). Requires at least two items."""
    if len(crumbs) < 2:
        return None

    elements: list[dict[str, Any]] = []
    for index, (name, url) in enumerate(crumbs, start=1):
        label = clean_structured_text(name)
        loc = settings.canonical_url(url)
        if not label or not loc:
            return None
        elements.append(
            {
                "@type": "ListItem",
                "position": index,
                "name": label,
                "item": loc,
            }
        )

    canonical = settings.canonical_url(page_url or crumbs[-1][1])
    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "BreadcrumbList",
        "@id": f"{canonical}#breadcrumb",
        "itemListElement": elements,
    }


def build_article_schema(
    settings: Settings,
    *,
    canonical_url: str,
    headline: str,
    description: str | None = None,
    date_published: datetime | date | None = None,
    date_modified: datetime | date | None = None,
    article_section: str | None = None,
    author: dict[str, Any] | None = None,
    image_urls: list[str] | None = None,
    keywords: list[str] | None = None,
) -> dict[str, Any] | None:
    page_url = settings.canonical_url(canonical_url)
    title = clean_structured_text(headline)
    if not page_url or not title:
        return None

    published = format_schema_date(date_published, timezone=settings.timezone)
    modified: str | None = None
    if date_modified is not None and date_published is not None:
        if _to_aware(date_modified, settings.timezone) >= _to_aware(
            date_published, settings.timezone
        ):
            modified = format_schema_date(date_modified, timezone=settings.timezone)
    elif date_modified is not None:
        modified = format_schema_date(date_modified, timezone=settings.timezone)

    data: dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Article",
        "@id": f"{page_url}#article",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": page_url,
        },
        "headline": title,
        "description": clean_structured_text(description),
        "url": page_url,
        "inLanguage": "ko-KR",
        "isAccessibleForFree": True,
        "datePublished": published,
        "dateModified": modified,
        "articleSection": clean_structured_text(article_section),
        "publisher": clips_organization_ref(settings),
        "author": author,
    }
    if image_urls:
        images = [settings.canonical_url(url) for url in image_urls if url]
        images = [url for url in images if url]
        if images:
            data["image"] = images
    if keywords:
        cleaned_keywords = [
            kw for kw in (clean_structured_text(item) for item in keywords) if kw
        ]
        if cleaned_keywords:
            data["keywords"] = cleaned_keywords
    return data


def build_news_article_schema(
    settings: Settings,
    *,
    item: NewsItem,
    page_url: str,
    description: str,
) -> dict[str, Any] | None:
    """Public news / notice / event / patch detail Article."""
    return build_article_schema(
        settings,
        canonical_url=page_url,
        headline=item.title,
        description=description,
        date_published=item.published_at,
        date_modified=item.updated_at,
        article_section=_ARTICLE_SECTION.get(item.category),
        author=clips_organization_author(settings),
    )


def build_guide_article_schema(
    settings: Settings,
    *,
    guide: GuideEntry,
    page_url: str,
    description: str,
) -> dict[str, Any] | None:
    """Published guide detail Article only."""
    if guide.status != "published":
        return None

    author_name = clean_structured_text(guide.author_name)
    if author_name and author_name.upper() != SERVICE_NAME:
        author: dict[str, Any] = {"@type": "Person", "name": author_name}
    else:
        author = clips_organization_author(settings)

    return build_article_schema(
        settings,
        canonical_url=page_url,
        headline=guide.title,
        description=description,
        date_published=guide.published_at,
        date_modified=guide.updated_at,
        article_section=guide.category_label or guide.category,
        author=author,
        keywords=list(guide.tags) if guide.tags else None,
    )


def build_home_structured_data(settings: Settings) -> list[dict[str, Any]]:
    return collect_json_ld_items(
        build_website_schema(settings),
        build_organization_schema(settings),
    )


def collect_json_ld_items(*items: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Prune empties and swallow builder failures so HTML still renders."""
    collected: list[dict[str, Any]] = []
    for item in items:
        if not item:
            continue
        try:
            pruned = prune_empty(item)
            if isinstance(pruned, dict) and pruned:
                collected.append(pruned)
        except Exception:
            logger.exception("Failed to prepare JSON-LD item; skipping")
    return collected
