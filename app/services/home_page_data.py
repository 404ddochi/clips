"""Home page hub view-model (public catalogue adapters)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.services.content_types import CATEGORY_LIST_META, NewsCategory
from app.services.coupon_mock_data import list_coupons
from app.services.guide_data import list_published_guides
from app.services.news_mock_data import detail_route_for, get_latest_by_category, list_news
from app.services.patch_mock_data import list_patch_notes, patch_type_labels
from app.services.seo import meta_description

logger = logging.getLogger(__name__)

NEWS_LIMIT = 4
PATCH_LIMIT = 3
COUPON_LIMIT = 4
GUIDE_LIMIT = 4


@dataclass(frozen=True, slots=True)
class QuickLinkItem:
    title: str
    description: str
    route_name: str
    icon: str


@dataclass(frozen=True, slots=True)
class HomeNewsItem:
    badge: str
    badge_variant: str
    title: str
    summary: str
    published_at: datetime
    detail_route: str
    slug: str
    url_path: str


@dataclass(frozen=True, slots=True)
class HomePatchItem:
    title: str
    summary: str
    version: str
    type_labels: tuple[str, ...]
    published_at: datetime
    slug: str
    url_path: str


@dataclass(frozen=True, slots=True)
class HomeCouponItem:
    title: str
    code: str
    reward_summary: str
    status_label: str
    valid_until: datetime
    slug: str
    url_path: str


@dataclass(frozen=True, slots=True)
class HomeGuideItem:
    title: str
    summary: str
    category_label: str
    author_name: str
    published_at: datetime
    slug: str
    url_path: str


@dataclass(frozen=True, slots=True)
class HomePageData:
    menu_links: tuple[QuickLinkItem, ...]
    latest_news: tuple[HomeNewsItem, ...]
    latest_patch_notes: tuple[HomePatchItem, ...]
    active_coupons: tuple[HomeCouponItem, ...]
    latest_guides: tuple[HomeGuideItem, ...]


# Major info menu — coupons/news covered by dedicated hub sections.
HOME_MENU_LINKS: tuple[QuickLinkItem, ...] = (
    QuickLinkItem(
        "클래스",
        "전투 스타일과 클래스 특징을 확인하세요.",
        "classes",
        "class",
    ),
    QuickLinkItem(
        "콘텐츠",
        "주요 성장 및 전투 콘텐츠를 확인하세요.",
        "contents",
        "content",
    ),
    QuickLinkItem(
        "아이템",
        "장비와 아이템 정보를 찾아보세요.",
        "items",
        "item",
    ),
    QuickLinkItem(
        "보스",
        "보스 정보와 전투 관련 정보를 확인하세요.",
        "bosses",
        "boss",
    ),
    QuickLinkItem(
        "지도",
        "지역, 사냥터, 던전과 NPC 정보를 확인하세요.",
        "maps",
        "map",
    ),
    QuickLinkItem(
        "공략",
        "CLIPS가 정리한 플레이 공략을 확인하세요.",
        "guides",
        "guide",
    ),
)

# Backward-compatible aliases used by older tests/imports.
QUICK_LINKS = HOME_MENU_LINKS

_NEWS_BADGE: dict[NewsCategory, tuple[str, str]] = {
    "notice": ("공지", "notice"),
    "event": ("이벤트", "event"),
}


def _safe_call[T](label: str, fn: Callable[[], T], default: T) -> T:
    try:
        return fn()
    except Exception:
        logger.exception("Home hub failed to load %s", label)
        return default


def build_latest_news(*, limit: int = NEWS_LIMIT) -> tuple[HomeNewsItem, ...]:
    items = [
        item
        for item in list_news()
        if item.category in ("notice", "event")
    ]
    items.sort(key=lambda item: item.published_at, reverse=True)
    result: list[HomeNewsItem] = []
    for item in items[:limit]:
        badge, variant = _NEWS_BADGE[item.category]
        path_prefix = CATEGORY_LIST_META[item.category]["path_prefix"]
        result.append(
            HomeNewsItem(
                badge=badge,
                badge_variant=variant,
                title=item.title,
                summary=meta_description(item.summary, fallback="", max_length=120),
                published_at=item.published_at,
                detail_route=detail_route_for(item.category),
                slug=item.slug,
                url_path=f"{path_prefix}/{item.slug}",
            )
        )
    return tuple(result)


def build_latest_patch_notes(*, limit: int = PATCH_LIMIT) -> tuple[HomePatchItem, ...]:
    result: list[HomePatchItem] = []
    for note in list_patch_notes()[:limit]:
        result.append(
            HomePatchItem(
                title=note.title,
                summary=meta_description(note.summary, fallback="", max_length=120),
                version=note.version,
                type_labels=patch_type_labels(note.patch_types),
                published_at=note.published_at,
                slug=note.slug,
                url_path=f"/news/patch-notes/{note.slug}",
            )
        )
    return tuple(result)


def build_active_coupons(*, limit: int = COUPON_LIMIT) -> tuple[HomeCouponItem, ...]:
    usable = [
        *list_coupons(status="available"),
        *list_coupons(status="expiring"),
    ]
    usable.sort(key=lambda item: item.valid_until)
    result: list[HomeCouponItem] = []
    for item in usable[:limit]:
        result.append(
            HomeCouponItem(
                title=item.title,
                code=item.code,
                reward_summary=meta_description(
                    item.reward_summary,
                    fallback="",
                    max_length=100,
                ),
                status_label=item.status_label,
                valid_until=item.valid_until,
                slug=item.slug,
                url_path=f"/coupons/{item.slug}",
            )
        )
    return tuple(result)


def build_latest_guides(*, limit: int = GUIDE_LIMIT) -> tuple[HomeGuideItem, ...]:
    guides = list(list_published_guides())
    guides.sort(
        key=lambda guide: (guide.published_at, guide.updated_at),
        reverse=True,
    )
    result: list[HomeGuideItem] = []
    for guide in guides[:limit]:
        result.append(
            HomeGuideItem(
                title=guide.title,
                summary=meta_description(guide.summary, fallback="", max_length=120),
                category_label=guide.category_label or "공략",
                author_name=guide.author_name,
                published_at=guide.published_at,
                slug=guide.slug,
                url_path=f"/guides/{guide.slug}",
            )
        )
    return tuple(result)


def build_home_page_data() -> HomePageData:
    """Assemble hub sections; isolate per-section failures."""
    empty_news: tuple[HomeNewsItem, ...] = ()
    empty_patches: tuple[HomePatchItem, ...] = ()
    empty_coupons: tuple[HomeCouponItem, ...] = ()
    empty_guides: tuple[HomeGuideItem, ...] = ()
    return HomePageData(
        menu_links=HOME_MENU_LINKS,
        latest_news=_safe_call("latest_news", build_latest_news, empty_news),
        latest_patch_notes=_safe_call(
            "latest_patch_notes",
            build_latest_patch_notes,
            empty_patches,
        ),
        active_coupons=_safe_call("active_coupons", build_active_coupons, empty_coupons),
        latest_guides=_safe_call("latest_guides", build_latest_guides, empty_guides),
    )


# --- Legacy helpers kept for compatibility ---


@dataclass(frozen=True, slots=True)
class NewsPlaceholderItem:
    badge: str
    badge_variant: str
    title: str
    summary: str
    status_text: str
    detail_route: str
    slug: str


@dataclass(frozen=True, slots=True)
class FeatureItem:
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class ArchiveTeaserItem:
    title: str
    status_text: str
    route_name: str


@dataclass(frozen=True, slots=True)
class InfoStripItem:
    label: str
    text: str
    route_name: str
    icon: str


PLATFORM_FEATURES: tuple[FeatureItem, ...] = (
    FeatureItem(
        "빠른 공식 소식 정리",
        "공지·이벤트·업데이트를 출처와 함께 빠르게 확인합니다.",
    ),
    FeatureItem(
        "클래스와 스킬 정보",
        "클래스별 특징과 스킬 정보를 읽기 쉽게 제공합니다.",
    ),
    FeatureItem(
        "보스와 콘텐츠 공략",
        "보스·던전·성장 콘텐츠를 카드와 목록으로 탐색합니다.",
    ),
    FeatureItem(
        "쿠폰과 이벤트 모음",
        "쿠폰 코드와 이벤트 안내를 한곳에서 찾습니다.",
    ),
)

ARCHIVE_TEASERS: tuple[ArchiveTeaserItem, ...] = (
    ArchiveTeaserItem("클래스", "데이터 준비 중", "classes"),
    ArchiveTeaserItem("아이템", "데이터 준비 중", "items"),
    ArchiveTeaserItem("보스", "데이터 준비 중", "bosses"),
    ArchiveTeaserItem("지역", "데이터 준비 중", "maps"),
)


def build_home_news_items() -> tuple[NewsPlaceholderItem, ...]:
    """Legacy one-per-category teaser (includes patch). Prefer build_latest_news."""
    items: list[NewsPlaceholderItem] = []
    slots: tuple[tuple[NewsCategory, str, str], ...] = (
        ("notice", "공지", "notice"),
        ("event", "이벤트", "event"),
        ("patch", "업데이트", "update"),
    )
    for category, badge, variant in slots:
        latest = get_latest_by_category(category)
        if latest is None:
            continue
        items.append(
            NewsPlaceholderItem(
                badge=badge,
                badge_variant=variant,
                title=latest.title,
                summary=latest.summary,
                status_text=latest.status_label,
                detail_route=detail_route_for(category),
                slug=latest.slug,
            )
        )
    return tuple(items)


def build_home_info_strip() -> tuple[InfoStripItem, ...]:
    notice = get_latest_by_category("notice")
    event = get_latest_by_category("event")
    patch = get_latest_by_category("patch")
    coupons = list_coupons(status="available")
    coupon_text = coupons[0].title if coupons else "쿠폰 준비 중"
    return (
        InfoStripItem(
            "최신 공지",
            notice.title if notice else "공지 준비 중",
            "news_notices",
            "notice",
        ),
        InfoStripItem(
            "이벤트",
            event.title if event else "이벤트 준비 중",
            "news_events",
            "event",
        ),
        InfoStripItem(
            "패치노트",
            patch.title if patch else "패치 준비 중",
            "news_patch_notes",
            "update",
        ),
        InfoStripItem("쿠폰", coupon_text, "coupons", "coupon"),
    )
