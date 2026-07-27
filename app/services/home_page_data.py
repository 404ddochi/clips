"""Home page view-model data (no DB)."""

from __future__ import annotations

from dataclasses import dataclass


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
    route_name: str


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


INFO_STRIP_ITEMS: tuple[InfoStripItem, ...] = (
    InfoStripItem("최신 공지", "수집·연동 준비 중", "news", "notice"),
    InfoStripItem("이벤트", "일정 정리 준비 중", "news", "event"),
    InfoStripItem("패치노트", "요약 공개 예정", "news", "update"),
    InfoStripItem("쿠폰", "코드 모음 준비 중", "coupons", "coupon"),
)

QUICK_LINKS: tuple[QuickLinkItem, ...] = (
    QuickLinkItem("클래스", "스킬·역할 정보", "classes", "class"),
    QuickLinkItem("콘텐츠", "던전·성장 안내", "contents", "content"),
    QuickLinkItem("아이템", "장비·재료 정리", "items", "item"),
    QuickLinkItem("보스", "패턴·드랍 정보", "bosses", "boss"),
    QuickLinkItem("지도", "지역·채집 정보", "maps", "map"),
    QuickLinkItem("공략", "팁·가이드 모음", "guides", "guide"),
    QuickLinkItem("쿠폰", "코드·사용 안내", "coupons", "coupon"),
    QuickLinkItem("업데이트", "패치·변경 요약", "news", "update"),
)

NEWS_PLACEHOLDERS: tuple[NewsPlaceholderItem, ...] = (
    NewsPlaceholderItem(
        badge="공지",
        badge_variant="notice",
        title="공식 소식 수집 준비 중",
        summary="주요 공지를 빠르게 확인할 수 있도록 준비하고 있습니다.",
        status_text="연동 준비 중",
        route_name="news",
    ),
    NewsPlaceholderItem(
        badge="이벤트",
        badge_variant="event",
        title="이벤트 정보 정리 준비 중",
        summary="진행 이벤트와 보상 정보를 한곳에서 볼 수 있게 구성합니다.",
        status_text="콘텐츠 준비 중",
        route_name="news",
    ),
    NewsPlaceholderItem(
        badge="업데이트",
        badge_variant="update",
        title="패치 노트 요약 준비 중",
        summary="업데이트 요약과 원문 링크를 함께 제공할 예정입니다.",
        status_text="정리 준비 중",
        route_name="news",
    ),
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
