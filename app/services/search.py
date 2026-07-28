"""Unified site search — public catalogue adapters and ranking."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from urllib.parse import urlencode

from app.services.boss_data import list_bosses
from app.services.class_data import list_classes
from app.services.coming_soon_data import get_coming_soon_page
from app.services.content_types import (
    CATEGORY_LIST_META,
    NewsCategory,
    NewsItem,
)
from app.services.coupon_mock_data import list_coupons
from app.services.guide_data import list_published_guides
from app.services.item_data import list_items
from app.services.map_data import list_regions
from app.services.news_mock_data import list_news
from app.services.seo import meta_description

logger = logging.getLogger(__name__)

SearchContentType = Literal[
    "notices",
    "events",
    "patch_notes",
    "classes",
    "contents",
    "items",
    "bosses",
    "maps",
    "guides",
    "coupons",
]

MAX_QUERY_LENGTH = 100
PER_TYPE_LIMIT = 5
TOTAL_LIMIT = 40

_WHITESPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")

# Display order for result groups.
SEARCH_TYPE_ORDER: tuple[SearchContentType, ...] = (
    "notices",
    "events",
    "patch_notes",
    "classes",
    "contents",
    "items",
    "bosses",
    "maps",
    "guides",
    "coupons",
)

SEARCH_TYPE_LABELS: dict[SearchContentType, str] = {
    "notices": "공지",
    "events": "이벤트",
    "patch_notes": "패치노트",
    "classes": "클래스",
    "contents": "콘텐츠",
    "items": "아이템",
    "bosses": "보스",
    "maps": "지도",
    "guides": "공략",
    "coupons": "쿠폰",
}

# UI filter chips (type query). "news" expands to all news-family types.
FILTER_CHIPS: tuple[tuple[str, str], ...] = (
    ("all", "전체"),
    ("news", "소식"),
    ("classes", "클래스"),
    ("contents", "콘텐츠"),
    ("items", "아이템"),
    ("bosses", "보스"),
    ("maps", "지도"),
    ("guides", "공략"),
    ("coupons", "쿠폰"),
)

_FILTER_TO_TYPES: dict[str, tuple[SearchContentType, ...]] = {
    "all": SEARCH_TYPE_ORDER,
    "news": ("notices", "events", "patch_notes"),
    "notices": ("notices",),
    "events": ("events",),
    "patch_notes": ("patch_notes",),
    "classes": ("classes",),
    "contents": ("contents",),
    "items": ("items",),
    "bosses": ("bosses",),
    "maps": ("maps",),
    "guides": ("guides",),
    "coupons": ("coupons",),
}

_NEWS_CATEGORY_TO_TYPE: dict[NewsCategory, SearchContentType] = {
    "notice": "notices",
    "event": "events",
    "patch": "patch_notes",
}


@dataclass(frozen=True, slots=True)
class SearchResultItem:
    content_type: SearchContentType
    content_type_label: str
    title: str
    summary: str
    url: str
    badge: str = ""
    published_at: datetime | None = None
    source_name: str = ""
    matched_field: str = ""
    relevance_score: int = 0
    image_url: str = ""


@dataclass(frozen=True, slots=True)
class SearchResultGroup:
    content_type: SearchContentType
    label: str
    results: tuple[SearchResultItem, ...]
    total_count: int
    displayed_count: int


@dataclass(frozen=True, slots=True)
class SearchResponse:
    query: str
    groups: tuple[SearchResultGroup, ...]
    total_count: int
    displayed_count: int
    searched_types: tuple[SearchContentType, ...]
    type_filter: str
    error: str = ""


@dataclass(frozen=True, slots=True)
class NormalizedQuery:
    raw: str
    normalized: str
    error: str = ""
    should_search: bool = False


def escape_like_wildcards(value: str) -> str:
    """Escape SQL LIKE wildcards for future DB-backed search."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def normalize_search_query(raw: str | None) -> NormalizedQuery:
    original = raw if raw is not None else ""
    cleaned = _TAG_RE.sub(" ", original)
    cleaned = html.unescape(cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return NormalizedQuery(raw=original, normalized="", should_search=False)
    if len(cleaned) > MAX_QUERY_LENGTH:
        return NormalizedQuery(
            raw=original,
            normalized=cleaned,
            error="검색어는 100자 이하여야 합니다.",
            should_search=False,
        )
    return NormalizedQuery(
        raw=original,
        normalized=cleaned,
        should_search=True,
    )


def resolve_type_filter(raw: str | None) -> str:
    key = (raw or "all").strip().casefold()
    if key in _FILTER_TO_TYPES:
        return key
    return "all"


def build_search_url(*, query: str = "", type_filter: str = "all") -> str:
    params: dict[str, str] = {}
    if query:
        params["q"] = query
    if type_filter and type_filter != "all":
        params["type"] = type_filter
    if not params:
        return "/search"
    return f"/search?{urlencode(params)}"


def search_filter_tabs(*, query: str = "", type_filter: str = "all") -> list[dict[str, str]]:
    return [
        {
            "key": key,
            "label": label,
            "href": build_search_url(query=query, type_filter=key),
            "current": "true" if key == type_filter else "false",
        }
        for key, label in FILTER_CHIPS
    ]


def _score_text(query: str, *, title: str, extras: tuple[str, ...] = ()) -> tuple[int, str]:
    q = query.casefold()
    title_cf = title.casefold()
    if not q:
        return 0, ""
    if title_cf == q:
        return 100, "title"
    if title_cf.startswith(q):
        return 80, "title"
    if q in title_cf:
        return 60, "title"
    for extra in extras:
        text = (extra or "").casefold()
        if text and q in text:
            return 30, "summary"
    return 0, ""


def _plain_summary(text: str | None, *, fallback: str = "") -> str:
    return meta_description(text, fallback=fallback, max_length=140)


def _sort_key(item: SearchResultItem) -> tuple[int, float, str]:
    stamp = item.published_at.timestamp() if item.published_at is not None else 0.0
    return (-item.relevance_score, -stamp, item.title.casefold())


def _news_url(item: NewsItem) -> str:
    meta = CATEGORY_LIST_META[item.category]
    return f"{meta['path_prefix']}/{item.slug}"


def _search_news(query: str) -> list[SearchResultItem]:
    results: list[SearchResultItem] = []
    for item in list_news():
        content_type = _NEWS_CATEGORY_TO_TYPE[item.category]
        score, matched = _score_text(
            query,
            title=item.title,
            extras=(item.summary, item.source_name, item.badge_label),
        )
        if score <= 0:
            continue
        results.append(
            SearchResultItem(
                content_type=content_type,
                content_type_label=SEARCH_TYPE_LABELS[content_type],
                title=item.title,
                summary=_plain_summary(item.summary),
                url=_news_url(item),
                badge=item.badge_label,
                published_at=item.published_at,
                source_name=item.source_name,
                matched_field=matched,
                relevance_score=score,
            )
        )
    return results


def _search_classes(query: str) -> list[SearchResultItem]:
    results: list[SearchResultItem] = []
    for item in list_classes():
        score, matched = _score_text(
            query,
            title=item.name,
            extras=(item.name_en, item.summary, item.source_note),
        )
        if score <= 0:
            continue
        results.append(
            SearchResultItem(
                content_type="classes",
                content_type_label=SEARCH_TYPE_LABELS["classes"],
                title=item.name,
                summary=_plain_summary(item.summary),
                url=f"/classes/{item.slug}",
                badge="클래스",
                source_name=item.source_note,
                matched_field=matched,
                relevance_score=score,
            )
        )
    return results


def _search_contents(query: str) -> list[SearchResultItem]:
    page = get_coming_soon_page("contents")
    if page is None:
        return []
    score, matched = _score_text(
        query,
        title=page.label,
        extras=(page.page_title, page.page_description, *page.future_features),
    )
    if score <= 0:
        return []
    return [
        SearchResultItem(
            content_type="contents",
            content_type_label=SEARCH_TYPE_LABELS["contents"],
            title=page.page_title,
            summary=_plain_summary(page.page_description),
            url="/contents",
            badge="준비 중",
            matched_field=matched,
            relevance_score=score,
        )
    ]


def _search_items(query: str) -> list[SearchResultItem]:
    results: list[SearchResultItem] = []
    for item in list_items():
        score, matched = _score_text(
            query,
            title=item.name,
            extras=(item.name_en, item.summary, item.slot_or_purpose, item.acquisition),
        )
        if score <= 0:
            continue
        results.append(
            SearchResultItem(
                content_type="items",
                content_type_label=SEARCH_TYPE_LABELS["items"],
                title=item.name,
                summary=_plain_summary(item.summary),
                url=f"/items/{item.slug}",
                badge=item.category or "아이템",
                matched_field=matched,
                relevance_score=score,
            )
        )
    return results


def _search_bosses(query: str) -> list[SearchResultItem]:
    results: list[SearchResultItem] = []
    for item in list_bosses():
        score, matched = _score_text(
            query,
            title=item.name,
            extras=(item.name_en, item.summary, item.region, item.category),
        )
        if score <= 0:
            continue
        results.append(
            SearchResultItem(
                content_type="bosses",
                content_type_label=SEARCH_TYPE_LABELS["bosses"],
                title=item.name,
                summary=_plain_summary(item.summary),
                url=f"/bosses/{item.slug}",
                badge=item.category or "보스",
                matched_field=matched,
                relevance_score=score,
            )
        )
    return results


def _search_maps(query: str) -> list[SearchResultItem]:
    results: list[SearchResultItem] = []
    for item in list_regions():
        score, matched = _score_text(
            query,
            title=item.name,
            extras=(item.name_en, item.summary, item.world_label, item.region_kind),
        )
        if score <= 0:
            continue
        results.append(
            SearchResultItem(
                content_type="maps",
                content_type_label=SEARCH_TYPE_LABELS["maps"],
                title=item.name,
                summary=_plain_summary(item.summary),
                url=f"/maps/{item.slug}",
                badge=item.region_kind or "지도",
                matched_field=matched,
                relevance_score=score,
                image_url=item.map_image_url or "",
            )
        )
    return results


def _search_guides(query: str) -> list[SearchResultItem]:
    results: list[SearchResultItem] = []
    for guide in list_published_guides():
        extras = (
            guide.summary,
            guide.category_label,
            guide.category,
            *guide.tags,
        )
        score, matched = _score_text(query, title=guide.title, extras=extras)
        if score <= 0:
            # Tag / category as mid-weight match
            tag_blob = " ".join((guide.category_label, guide.category, *guide.tags)).casefold()
            if query.casefold() in tag_blob:
                score, matched = 45, "tag"
            else:
                continue
        results.append(
            SearchResultItem(
                content_type="guides",
                content_type_label=SEARCH_TYPE_LABELS["guides"],
                title=guide.title,
                summary=_plain_summary(guide.summary),
                url=f"/guides/{guide.slug}",
                badge=guide.category_label or "공략",
                published_at=guide.published_at,
                source_name=guide.author_name,
                matched_field=matched,
                relevance_score=score,
            )
        )
    return results


def _search_coupons(query: str) -> list[SearchResultItem]:
    """Include all coupon statuses shown on /coupons (including expired)."""
    results: list[SearchResultItem] = []
    for item in list_coupons():
        score, matched = _score_text(
            query,
            title=item.title,
            extras=(item.reward_summary, item.code, item.status_label, item.source_name or ""),
        )
        if score <= 0:
            continue
        results.append(
            SearchResultItem(
                content_type="coupons",
                content_type_label=SEARCH_TYPE_LABELS["coupons"],
                title=item.title,
                summary=_plain_summary(item.reward_summary),
                url=f"/coupons/{item.slug}",
                badge=item.status_label,
                published_at=item.valid_from,
                source_name=item.source_name or "",
                matched_field=matched,
                relevance_score=score,
            )
        )
    return results


def search_all(
    query: str,
    *,
    type_filter: str = "all",
    per_type_limit: int = PER_TYPE_LIMIT,
    total_limit: int = TOTAL_LIMIT,
) -> SearchResponse:
    normalized = normalize_search_query(query)
    resolved_filter = resolve_type_filter(type_filter)
    searched_types = _FILTER_TO_TYPES[resolved_filter]

    if normalized.error:
        return SearchResponse(
            query=normalized.normalized,
            groups=(),
            total_count=0,
            displayed_count=0,
            searched_types=searched_types,
            type_filter=resolved_filter,
            error=normalized.error,
        )
    if not normalized.should_search:
        return SearchResponse(
            query="",
            groups=(),
            total_count=0,
            displayed_count=0,
            searched_types=searched_types,
            type_filter=resolved_filter,
        )

    q = normalized.normalized
    by_type: dict[SearchContentType, list[SearchResultItem]] = {
        key: [] for key in SEARCH_TYPE_ORDER
    }

    try:
        news_results = _search_news(q)
        for item in news_results:
            by_type[item.content_type].append(item)
    except Exception:
        logger.exception("Unified search failed for news family")

    for content_type, adapter in (
        ("classes", _search_classes),
        ("contents", _search_contents),
        ("items", _search_items),
        ("bosses", _search_bosses),
        ("maps", _search_maps),
        ("guides", _search_guides),
        ("coupons", _search_coupons),
    ):
        if content_type not in searched_types:
            continue
        try:
            by_type[content_type].extend(adapter(q))
        except Exception:
            logger.exception("Unified search failed for type=%s", content_type)

    # Restrict news-family buckets when filtering a subset.
    for news_type in ("notices", "events", "patch_notes"):
        if news_type not in searched_types:
            by_type[news_type] = []

    groups: list[SearchResultGroup] = []
    displayed_total = 0
    match_total = 0

    for content_type in SEARCH_TYPE_ORDER:
        if content_type not in searched_types:
            continue
        items = sorted(by_type[content_type], key=_sort_key)
        if not items:
            continue
        total = len(items)
        match_total += total
        remaining = max(total_limit - displayed_total, 0)
        limit = min(per_type_limit, remaining)
        shown = tuple(items[:limit]) if limit > 0 else ()
        if not shown:
            # Still count toward totals but skip empty display groups when over cap.
            continue
        displayed_total += len(shown)
        groups.append(
            SearchResultGroup(
                content_type=content_type,
                label=SEARCH_TYPE_LABELS[content_type],
                results=shown,
                total_count=total,
                displayed_count=len(shown),
            )
        )

    return SearchResponse(
        query=q,
        groups=tuple(groups),
        total_count=match_total,
        displayed_count=displayed_total,
        searched_types=searched_types,
        type_filter=resolved_filter,
    )
