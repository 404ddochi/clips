"""SEO builders for information pages (mock-safe)."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.services.content_types import NewsItem


def build_breadcrumb_json_ld(
    settings: Settings,
    crumbs: list[tuple[str, str]],
) -> dict[str, Any]:
    """crumbs: list of (name, absolute_url)."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(crumbs, start=1)
        ],
    }


def build_article_json_ld(
    settings: Settings,
    *,
    item: NewsItem,
    page_url: str,
) -> dict[str, Any]:
    """NewsArticle-shaped data without claiming official publisher status."""
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": item.title,
        "description": item.summary,
        "datePublished": item.published_at.date().isoformat(),
        "inLanguage": "ko",
        "url": page_url,
        "isAccessibleForFree": True,
        "author": {
            "@type": "Organization",
            "name": "CLIPS Mock",
        },
        "publisher": {
            "@type": "Organization",
            "name": "CLIPS",
        },
        "about": {
            "@type": "VideoGame",
            "name": "이클립스: 더 어웨이크닝",
            "alternateName": "Eclipse: The Awakening",
        },
    }
    if item.updated_at is not None:
        data["dateModified"] = item.updated_at.date().isoformat()
    return data
