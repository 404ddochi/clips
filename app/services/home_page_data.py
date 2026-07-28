"""Home page view-model data (no DB). Linked to mock content sources."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.content_types import NewsCategory
from app.services.coupon_mock_data import list_coupons
from app.services.news_mock_data import detail_route_for, get_latest_by_category


@dataclass(frozen=True, slots=True)
class QuickLinkItem:
    title: str
    description: str
    route_name: str
    icon: str


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


QUICK_LINKS: tuple[QuickLinkItem, ...] = (
    QuickLinkItem("클래스", "스킬·역할 정보", "classes", "class"),
    QuickLinkItem("콘텐츠", "던전·성장 안내", "contents", "content"),
    QuickLinkItem("아이템", "장비·재료 정리", "items", "item"),
    QuickLinkItem("보스", "패턴·드랍 정보", "bosses", "boss"),
    QuickLinkItem("지도", "지역·채집 정보", "maps", "map"),
    QuickLinkItem("공략", "팁·가이드 모음", "guides", "guide"),
    QuickLinkItem("쿠폰", "코드·사용 안내", "coupons", "coupon"),
    QuickLinkItem("업데이트", "패치·변경 요약", "news_patch_notes", "update"),
)

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

_HOME_NEWS_SLOTS: tuple[tuple[NewsCategory, str, str], ...] = (
    ("notice", "공지", "notice"),
    ("event", "이벤트", "event"),
    ("patch", "업데이트", "update"),
)


def build_home_news_items() -> tuple[NewsPlaceholderItem, ...]:
    items: list[NewsPlaceholderItem] = []
    for category, badge, variant in _HOME_NEWS_SLOTS:
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
    coupon_text = coupons[0].title if coupons else "Mock 쿠폰 준비"
    return (
        InfoStripItem(
            "최신 공지",
            notice.title if notice else "Mock 공지",
            "news_notices",
            "notice",
        ),
        InfoStripItem(
            "이벤트",
            event.title if event else "Mock 이벤트",
            "news_events",
            "event",
        ),
        InfoStripItem(
            "패치노트",
            patch.title if patch else "Mock 패치",
            "news_patch_notes",
            "update",
        ),
        InfoStripItem("쿠폰", coupon_text, "coupons", "coupon"),
    )
