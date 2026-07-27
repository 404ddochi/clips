"""Application-wide constants."""

from __future__ import annotations

from dataclasses import dataclass

SERVICE_NAME = "CLIPS"
SERVICE_NAME_KO = "클립스"
GAME_TITLE = "이클립스: 더 어웨이크닝"
DEFAULT_SECRET_KEY = "change-me"

DEFAULT_HOME_TITLE = "클립스 - 이클립스: 더 어웨이크닝 정보 사이트"
DEFAULT_HOME_DESCRIPTION = (
    "클립스는 이클립스: 더 어웨이크닝의 공지, 이벤트, 클래스, 콘텐츠, "
    "아이템, 보스, 공략과 쿠폰 정보를 제공하는 비공식 정보 사이트입니다."
)

DISCLAIMER_SHORT = (
    "CLIPS(클립스)는 공식 서비스가 아닌 비공식 팬 정보 사이트입니다. "
    "게임명 및 관련 명칭은 각 권리자의 자산입니다."
)


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    path: str
    key: str


MAIN_NAV: tuple[NavItem, ...] = (
    NavItem("홈", "/", "home"),
    NavItem("소식", "/news", "news"),
    NavItem("클래스", "/classes", "classes"),
    NavItem("콘텐츠", "/contents", "contents"),
    NavItem("아이템", "/items", "items"),
    NavItem("보스", "/bosses", "bosses"),
    NavItem("지도", "/maps", "maps"),
    NavItem("공략", "/guides", "guides"),
    NavItem("쿠폰", "/coupons", "coupons"),
)

PREPARING_SECTIONS: dict[str, str] = {
    "news": "소식",
    "classes": "클래스",
    "contents": "콘텐츠",
    "items": "아이템",
    "bosses": "보스",
    "maps": "지도",
    "guides": "공략",
    "coupons": "쿠폰",
}

INFO_MENU_CARDS: tuple[tuple[str, str, str], ...] = (
    ("클래스", "직업별 스킬과 성장 정보를 준비 중입니다.", "/classes"),
    ("콘텐츠", "던전과 성장 콘텐츠 정보를 준비 중입니다.", "/contents"),
    ("아이템", "장비와 재료 정보를 준비 중입니다.", "/items"),
    ("보스", "보스 패턴과 드랍 정보를 준비 중입니다.", "/bosses"),
    ("지도", "지역과 채집 정보를 준비 중입니다.", "/maps"),
    ("공략", "공략과 팁을 준비 중입니다.", "/guides"),
)

PLACEHOLDER_NEWS: tuple[tuple[str, str, str], ...] = (
    ("공지", "공식 공지 연동 준비 중", "공지·이벤트 수집 기능을 개발하고 있습니다."),
    ("업데이트", "패치 노트 정리 준비 중", "업데이트 요약과 원문 링크를 제공할 예정입니다."),
    ("이벤트", "이벤트 캘린더 준비 중", "진행 중인 이벤트를 한곳에서 확인할 수 있습니다."),
)

SITEMAP_PUBLIC_PATHS: tuple[str, ...] = ("/",)
