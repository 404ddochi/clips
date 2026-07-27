"""Application-wide constants."""

from __future__ import annotations

from dataclasses import dataclass

SERVICE_NAME = "CLIPS"
SERVICE_NAME_KO = "클립스"
GAME_TITLE = "이클립스: 더 어웨이크닝"
GAME_TITLE_EN = "Eclipse: The Awakening"
DEFAULT_SECRET_KEY = "change-me"

DEFAULT_HOME_TITLE = "CLIPS - 이클립스: 더 어웨이크닝 정보 사이트"
DEFAULT_HOME_DESCRIPTION = (
    "CLIPS는 이클립스: 더 어웨이크닝의 공지, 이벤트, 클래스, 아이템, "
    "보스, 지도, 공략, 쿠폰 정보를 제공하는 비공식 정보 플랫폼입니다."
)

FOOTER_DISCLAIMER = (
    "CLIPS(클립스)는 이클립스: 더 어웨이크닝의 비공식 정보 플랫폼이며, "
    "게임의 상표와 저작권은 각 권리자에게 있습니다."
)


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

SITEMAP_PUBLIC_PATHS: tuple[str, ...] = ("/",)
