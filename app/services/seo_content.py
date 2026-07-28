"""Compatibility wrappers for structured data builders."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.services.content_types import NewsItem
from app.services.structured_data import (
    build_breadcrumb_schema,
    build_news_article_schema,
    collect_json_ld_items,
)


def build_breadcrumb_json_ld(
    settings: Settings,
    crumbs: list[tuple[str, str]],
) -> dict[str, Any]:
    """crumbs: list of (name, absolute_url)."""
    schema = build_breadcrumb_schema(settings, crumbs)
    return schema or {}


def build_article_json_ld(
    settings: Settings,
    *,
    item: NewsItem,
    page_url: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Article JSON-LD for public news-family detail pages."""
    schema = build_news_article_schema(
        settings,
        item=item,
        page_url=page_url,
        description=description or item.summary,
    )
    return schema or {}


def as_structured_data(*items: dict[str, Any] | None) -> list[dict[str, Any]]:
    return collect_json_ld_items(*items)
