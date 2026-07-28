"""Shared content types for mock information pages (future DB-ready)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

NewsCategory = Literal["notice", "event", "patch"]
CouponStatus = Literal["available", "expiring", "expired"]
ArticleBlockKind = Literal[
    "paragraph",
    "heading2",
    "heading3",
    "list",
    "olist",
    "quote",
    "callout",
    "note",
]


@dataclass(frozen=True, slots=True)
class ArticleBlock:
    kind: ArticleBlockKind
    text: str = ""
    items: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NewsItem:
    slug: str
    category: NewsCategory
    title: str
    summary: str
    published_at: datetime
    updated_at: datetime | None
    source_name: str
    source_url: str | None
    is_featured: bool
    status_label: str
    body: tuple[ArticleBlock, ...]
    badge_label: str
    badge_variant: str


@dataclass(frozen=True, slots=True)
class CouponItem:
    slug: str
    code: str
    title: str
    reward_summary: str
    valid_from: datetime
    valid_until: datetime
    status: CouponStatus
    status_label: str
    source_name: str | None
    source_url: str | None
    body: tuple[ArticleBlock, ...]
    usage_notes: tuple[str, ...]


CouponFilterKey = Literal["all", "available", "expiring", "expired"]

COUPON_STATUS_FILTERS: tuple[tuple[CouponFilterKey, str], ...] = (
    ("all", "전체"),
    ("available", "사용 가능"),
    ("expiring", "만료 임박"),
    ("expired", "종료"),
)

COUPON_STATUS_LABELS: dict[CouponStatus, str] = {
    "available": "사용 가능",
    "expiring": "만료 임박",
    "expired": "종료",
}


@dataclass(frozen=True, slots=True)
class CategoryTab:
    key: str
    label: str
    route_name: str


NEWS_CATEGORY_TABS: tuple[CategoryTab, ...] = (
    CategoryTab("all", "전체", "news"),
    CategoryTab("notice", "공지", "news_notices"),
    CategoryTab("event", "이벤트", "news_events"),
    CategoryTab("patch", "패치노트", "news_patch_notes"),
)

CATEGORY_LIST_META: dict[NewsCategory, dict[str, str]] = {
    "notice": {
        "title": "공지",
        "description": "CLIPS Mock 공지 목록입니다. 실제 공식 공지가 아닙니다.",
        "route_name": "news_notices",
        "detail_route": "news_notice_detail",
        "path_prefix": "/news/notices",
    },
    "event": {
        "title": "이벤트",
        "description": "CLIPS Mock 이벤트 목록입니다. 실제 이벤트 일정이 아닙니다.",
        "route_name": "news_events",
        "detail_route": "news_event_detail",
        "path_prefix": "/news/events",
    },
    "patch": {
        "title": "패치노트",
        "description": "CLIPS Mock 패치노트 목록입니다. 실제 업데이트 내용이 아닙니다.",
        "route_name": "news_patch_notes",
        "detail_route": "news_patch_detail",
        "path_prefix": "/news/patch-notes",
    },
}

PAGE_TITLE_SUFFIX = "CLIPS - 이클립스: 더 어웨이크닝"
MOCK_ROBOTS = "noindex, follow"

# —— Classes ——
ClassStyle = Literal["melee", "ranged", "magic", "support"]
ClassFilterKey = Literal["all", "melee", "ranged", "magic", "support"]
ClassAccent = Literal["melee", "ranged", "magic", "support"]

CLASS_STYLE_LABELS: dict[ClassStyle, str] = {
    "melee": "근거리",
    "ranged": "원거리",
    "magic": "마법",
    "support": "지원",
}

CLASS_STYLE_FILTERS: tuple[tuple[ClassFilterKey, str], ...] = (
    ("all", "전체"),
    ("melee", "근거리"),
    ("ranged", "원거리"),
    ("magic", "마법"),
    ("support", "지원"),
)

CLASS_PENDING_LABEL = "공식 정보 공개 후 업데이트 예정"


@dataclass(frozen=True, slots=True)
class ClassItem:
    """Playable class entry from publicly disclosed information only."""

    slug: str
    name: str
    name_en: str
    symbol: str
    accent: ClassAccent
    styles: tuple[ClassStyle, ...]
    weapons: tuple[str, ...]
    combat_styles: tuple[str, ...]
    summary: str
    source_note: str
    weapons_pending: bool = False
    combat_styles_pending: bool = False
    summary_pending: bool = False


# —— Patch notes (timeline list) ——
PatchType = Literal["update", "balance", "bugfix", "system", "event"]
PatchFilterKey = Literal["all", "update", "balance", "bugfix", "system", "event"]

PATCH_TYPE_LABELS: dict[PatchType, str] = {
    "update": "업데이트",
    "balance": "밸런스",
    "bugfix": "버그 수정",
    "system": "시스템",
    "event": "이벤트",
}

PATCH_TYPE_FILTERS: tuple[tuple[PatchFilterKey, str], ...] = (
    ("all", "전체"),
    ("update", "업데이트"),
    ("balance", "밸런스"),
    ("bugfix", "버그 수정"),
    ("system", "시스템"),
    ("event", "이벤트"),
)


@dataclass(frozen=True, slots=True)
class PatchChangeItem:
    """A single change bullet on a mock patch note."""

    title: str
    summary: str = ""


@dataclass(frozen=True, slots=True)
class PatchNote:
    """Mock patch note for Patch Timeline (not official game content)."""

    slug: str
    version: str
    title: str
    summary: str
    published_at: datetime
    patch_types: tuple[PatchType, ...]
    changes: tuple[PatchChangeItem, ...]
    keywords: tuple[str, ...] = ()
    body: tuple[ArticleBlock, ...] = ()
    source_name: str = "CLIPS Mock"
    source_url: str | None = None
    is_featured: bool = False
    status_label: str = "샘플"
