"""Coming-soon page metadata per section."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ComingSoonPage:
    section_key: str
    label: str
    route_name: str
    page_title: str
    page_description: str
    icon: str
    future_features: tuple[str, ...]


COMING_SOON_PAGES: dict[str, ComingSoonPage] = {
    "news": ComingSoonPage(
        section_key="news",
        label="소식",
        route_name="news",
        page_title="소식",
        page_description="공지, 이벤트, 업데이트 소식을 한곳에서 확인할 수 있도록 준비 중입니다.",
        icon="news",
        future_features=(
            "공식 공지·이벤트 요약과 원문 링크",
            "업데이트·패치 노트 정리",
            "출처 표기와 중복 방지",
        ),
    ),
    "classes": ComingSoonPage(
        section_key="classes",
        label="클래스",
        route_name="classes",
        page_title="클래스",
        page_description="클래스별 특징, 스킬, 성장 정보를 제공할 예정입니다.",
        icon="class",
        future_features=("클래스 개요와 역할", "스킬 목록과 설명", "성장·전직 정보"),
    ),
    "contents": ComingSoonPage(
        section_key="contents",
        label="콘텐츠",
        route_name="contents",
        page_title="콘텐츠",
        page_description="던전, 성장, 일일 콘텐츠 정보를 정리할 예정입니다.",
        icon="content",
        future_features=("콘텐츠 유형별 안내", "입장 조건과 보상 요약", "관련 공략 링크"),
    ),
    "items": ComingSoonPage(
        section_key="items",
        label="아이템",
        route_name="items",
        page_title="아이템",
        page_description="장비, 재료, 제작 정보를 아카이브 형태로 제공할 예정입니다.",
        icon="item",
        future_features=("아이템 분류와 검색", "획득처·용도 요약", "제작·강화 연계 정보"),
    ),
    "bosses": ComingSoonPage(
        section_key="bosses",
        label="보스",
        route_name="bosses",
        page_title="보스",
        page_description="보스 패턴, 드랍, 공략 요약을 제공할 예정입니다.",
        icon="boss",
        future_features=("보스별 기본 정보", "패턴·약점 요약", "드랍 및 권장 전투력"),
    ),
    "maps": ComingSoonPage(
        section_key="maps",
        label="지도",
        route_name="maps",
        page_title="지도",
        page_description="지역, 이동, 채집·탐험 정보를 지도와 함께 제공할 예정입니다.",
        icon="map",
        future_features=("지역별 개요", "NPC·채집 포인트", "연계 퀘스트·콘텐츠"),
    ),
    "guides": ComingSoonPage(
        section_key="guides",
        label="공략",
        route_name="guides",
        page_title="공략",
        page_description="초보·성장·엔드 콘텐츠 공략을 모아 제공할 예정입니다.",
        icon="guide",
        future_features=("주제별 공략 목록", "단계별 가이드", "관련 데이터 링크"),
    ),
    "coupons": ComingSoonPage(
        section_key="coupons",
        label="쿠폰",
        route_name="coupons",
        page_title="쿠폰",
        page_description="쿠폰 코드와 사용 방법, 유효 기간을 정리할 예정입니다.",
        icon="coupon",
        future_features=("쿠폰 코드 목록", "사용 방법·주의사항", "만료·갱신 상태 표시"),
    ),
}


def get_coming_soon_page(section_key: str) -> ComingSoonPage | None:
    return COMING_SOON_PAGES.get(section_key)
