"""Application-wide constants."""

from __future__ import annotations

from dataclasses import dataclass

SERVICE_NAME = "CLIPS"
SERVICE_NAME_KO = "클립스"
GAME_TITLE = "이클립스: 더 어웨이크닝"
GAME_TITLE_EN = "Eclipse: The Awakening"
DEFAULT_SECRET_KEY = "change-me"

DEFAULT_HOME_TITLE = "CLIPS - 이클립스: 더 어웨이크닝 정보 플랫폼"
DEFAULT_HOME_DESCRIPTION = (
    "이클립스: 더 어웨이크닝의 소식, 클래스, 아이템, 보스, 지도, 공략과 "
    "쿠폰 정보를 확인할 수 있는 비공식 정보 플랫폼입니다."
)

# Public HTML robots (indexable catalogue / editorial pages).
PUBLIC_ROBOTS = "index, follow"
# Backward-compatible alias — public pages are indexable in SEO foundation.
MOCK_ROBOTS = PUBLIC_ROBOTS
NOINDEX_ROBOTS = "noindex, nofollow"

PAGE_DESCRIPTIONS: dict[str, str] = {
    "home": DEFAULT_HOME_DESCRIPTION,
    "news": "이클립스: 더 어웨이크닝의 최신 소식과 공식 공지를 CLIPS에서 확인하세요.",
    "patch_notes": (
        "이클립스: 더 어웨이크닝의 업데이트 및 패치노트를 날짜별로 확인하세요."
    ),
    "classes": "이클립스: 더 어웨이크닝의 클래스 특징과 관련 정보를 확인하세요.",
    "contents": "이클립스: 더 어웨이크닝의 주요 콘텐츠 정보를 확인하세요.",
    "items": "이클립스: 더 어웨이크닝의 장비와 아이템 정보를 확인하세요.",
    "bosses": "이클립스: 더 어웨이크닝의 보스와 전투 관련 정보를 확인하세요.",
    "maps": (
        "이클립스: 더 어웨이크닝의 지역, 월드맵, 사냥터, 던전과 NPC 정보를 확인하세요."
    ),
    "guides": (
        "CLIPS가 정리한 이클립스: 더 어웨이크닝의 비공식 공략과 플레이 정보를 확인하세요."
    ),
    "coupons": (
        "현재 사용할 수 있는 이클립스: 더 어웨이크닝 쿠폰과 보상 정보를 확인하세요."
    ),
}

# List paths always included in sitemap (stable order).
SITEMAP_PUBLIC_PATHS: tuple[str, ...] = (
    "/",
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
)

FOOTER_DISCLAIMER = (
    "CLIPS(클립스)는 이클립스: 더 어웨이크닝의 비공식 정보 플랫폼이며, "
    "게임의 상표와 저작권은 각 권리자에게 있습니다."
)


def page_title(page_name: str) -> str:
    """List/hub title: '{페이지명} - CLIPS'."""
    name = page_name.strip()
    if not name:
        return DEFAULT_HOME_TITLE
    if name.upper() == "CLIPS" or name.endswith(" - CLIPS"):
        return name if name.endswith(" - CLIPS") or name == DEFAULT_HOME_TITLE else name
    return f"{name} - CLIPS"


def detail_title(content_title: str) -> str:
    """Detail title: '{콘텐츠 제목} - CLIPS'."""
    title = content_title.strip()
    if not title:
        return DEFAULT_HOME_TITLE
    if title.endswith(" - CLIPS"):
        return title
    return f"{title} - CLIPS"



@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    route_name: str
    key: str


MAIN_NAV: tuple[NavItem, ...] = (
    NavItem("홈", "home", "home"),
    NavItem("소식", "news", "news"),
    NavItem("클래스", "classes", "classes"),
    NavItem("콘텐츠", "contents", "contents"),
    NavItem("아이템", "items", "items"),
    NavItem("보스", "bosses", "bosses"),
    NavItem("지도", "maps", "maps"),
    NavItem("공략", "guides", "guides"),
    NavItem("쿠폰", "coupons", "coupons"),
)
