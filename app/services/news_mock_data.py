"""Mock news / notice / event / patch data (not official content)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.content_types import (
    CATEGORY_LIST_META,
    ArticleBlock,
    NewsCategory,
    NewsItem,
)
from app.services.patch_mock_data import patch_notes_as_news_items

_D3 = datetime(2026, 7, 14, 15, 30, tzinfo=UTC)
_D4 = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
_D5 = datetime(2026, 7, 18, 13, 0, tzinfo=UTC)
_D6 = datetime(2026, 7, 20, 16, 0, tzinfo=UTC)


def _p(text: str) -> ArticleBlock:
    return ArticleBlock(kind="paragraph", text=text)


def _h2(text: str) -> ArticleBlock:
    return ArticleBlock(kind="heading2", text=text)


def _h3(text: str) -> ArticleBlock:
    return ArticleBlock(kind="heading3", text=text)


def _ul(*items: str) -> ArticleBlock:
    return ArticleBlock(kind="list", items=items)


def _ol(*items: str) -> ArticleBlock:
    return ArticleBlock(kind="olist", items=items)


def _callout(text: str) -> ArticleBlock:
    return ArticleBlock(kind="callout", text=text)


def _note(text: str) -> ArticleBlock:
    return ArticleBlock(kind="note", text=text)


def _quote(text: str) -> ArticleBlock:
    return ArticleBlock(kind="quote", text=text)


NEWS_ITEMS: tuple[NewsItem, ...] = (
    NewsItem(
        slug="clips-news-structure-sample",
        category="notice",
        title="소식 데이터 구조 검증용 샘플 공지",
        summary="CLIPS 정보 페이지 UI를 검증하기 위한 Mock 공지입니다. 공식 안내가 아닙니다.",
        published_at=_D6,
        updated_at=None,
        source_name="CLIPS Mock",
        source_url=None,
        is_featured=True,
        status_label="샘플",
        badge_label="공지",
        badge_variant="notice",
        body=(
            _p("이 문서는 CLIPS Phase 4에서 사용하는 예시 공지입니다."),
            _h2("Mock 안내"),
            _ul(
                "실제 게임 공지·이벤트·패치 내용이 아닙니다.",
                "목록·상세·SEO·브레드크럼 구조를 검증합니다.",
                "원문 링크는 의도적으로 비워 두었습니다.",
            ),
            _callout("공식 일정과 안내는 항상 공식 채널을 우선 확인해 주세요."),
            _note("CLIPS는 비공식 정보 플랫폼입니다."),
        ),
    ),
    NewsItem(
        slug="sample-notice-collection-prep",
        category="notice",
        title="공식 소식 수집 준비 안내 (샘플)",
        summary="공지 수집·연동 전 단계의 UI 샘플입니다. 실제 수집 상태가 아닙니다.",
        published_at=_D5,
        updated_at=_D5,
        source_name="CLIPS Mock",
        source_url=None,
        is_featured=False,
        status_label="준비 중",
        badge_label="공지",
        badge_variant="notice",
        body=(
            _p("본 페이지는 소식 수집 파이프라인 도입 전 UI를 점검하기 위한 예시입니다."),
            _h2("예정 기능 (예시)"),
            _ol("출처 표기", "중복 방지", "카테고리 분류"),
            _quote("샘플 인용문: 데이터 구조만 확인하세요."),
            _p("세부 스펙은 향후 DB·크롤러 단계에서 확정됩니다."),
        ),
    ),
    NewsItem(
        slug="sample-event-calendar-mock",
        category="event",
        title="이벤트 일정 카드 UI 샘플",
        summary="이벤트 목록·상세 레이아웃을 확인하기 위한 Mock입니다.",
        published_at=_D4,
        updated_at=None,
        source_name="CLIPS Mock",
        source_url=None,
        is_featured=True,
        status_label="샘플",
        badge_label="이벤트",
        badge_variant="event",
        body=(
            _p("이벤트 보상·기간 등은 예시 문장만 포함합니다."),
            _h2("샘플 섹션"),
            _h3("표시 항목"),
            _ul("기간 표기 UI", "보상 요약 슬롯", "출처 영역"),
            _callout("실제 진행 중인 이벤트가 아닙니다."),
        ),
    ),
    NewsItem(
        slug="sample-event-reward-layout",
        category="event",
        title="보상 요약 레이아웃 점검용 샘플",
        summary="이벤트 상세의 본문 계층과 메타 영역을 검증합니다.",
        published_at=_D3,
        updated_at=None,
        source_name="CLIPS Mock",
        source_url=None,
        is_featured=False,
        status_label="샘플",
        badge_label="이벤트",
        badge_variant="event",
        body=(
            _p("보상 수치는 의도적으로 넣지 않았습니다."),
            _p("가짜 수치로 공식 보상을 암시하지 않기 위함입니다."),
            _note("Mock 전용 콘텐츠입니다."),
        ),
    ),
    # Patch notes live in patch_mock_data (Patch Timeline source of truth).
    *patch_notes_as_news_items(),
)


def list_news(*, category: NewsCategory | None = None) -> tuple[NewsItem, ...]:
    items = NEWS_ITEMS
    if category is not None:
        items = tuple(item for item in items if item.category == category)
    return tuple(sorted(items, key=lambda item: item.published_at, reverse=True))


def get_news_by_slug(category: NewsCategory, slug: str) -> NewsItem | None:
    for item in NEWS_ITEMS:
        if item.category == category and item.slug == slug:
            return item
    return None


def get_featured_news() -> NewsItem | None:
    featured = [item for item in list_news() if item.is_featured]
    return featured[0] if featured else None


def get_latest_by_category(category: NewsCategory) -> NewsItem | None:
    items = list_news(category=category)
    return items[0] if items else None


def news_neighbors(
    category: NewsCategory,
    slug: str,
) -> tuple[NewsItem | None, NewsItem | None]:
    items = list_news(category=category)
    for index, item in enumerate(items):
        if item.slug == slug:
            prev_item = items[index + 1] if index + 1 < len(items) else None
            next_item = items[index - 1] if index > 0 else None
            return prev_item, next_item
    return None, None


def detail_route_for(category: NewsCategory) -> str:
    return CATEGORY_LIST_META[category]["detail_route"]


def related_news(item: NewsItem, *, limit: int = 3) -> tuple[NewsItem, ...]:
    others = [entry for entry in list_news(category=item.category) if entry.slug != item.slug]
    return tuple(others[:limit])
