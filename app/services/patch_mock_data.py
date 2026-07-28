"""Mock patch notes for Patch Timeline UI (not official update content)."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlencode

from app.services.content_types import (
    PATCH_TYPE_FILTERS,
    PATCH_TYPE_LABELS,
    ArticleBlock,
    NewsItem,
    PatchChangeItem,
    PatchFilterKey,
    PatchNote,
    PatchType,
)

_D1 = datetime(2026, 7, 22, 14, 0, tzinfo=UTC)
_D2 = datetime(2026, 7, 18, 11, 0, tzinfo=UTC)
_D3 = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
_D4 = datetime(2026, 7, 10, 9, 0, tzinfo=UTC)
_D5 = datetime(2026, 7, 6, 16, 0, tzinfo=UTC)
_D6 = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
_D7 = datetime(2026, 6, 28, 15, 30, tzinfo=UTC)


def _p(text: str) -> ArticleBlock:
    return ArticleBlock(kind="paragraph", text=text)


def _h2(text: str) -> ArticleBlock:
    return ArticleBlock(kind="heading2", text=text)


def _ul(*items: str) -> ArticleBlock:
    return ArticleBlock(kind="list", items=items)


def _callout(text: str) -> ArticleBlock:
    return ArticleBlock(kind="callout", text=text)


def _note(text: str) -> ArticleBlock:
    return ArticleBlock(kind="note", text=text)


# Development-only mock patches. Not official Eclipse patch notes.
PATCH_NOTES: tuple[PatchNote, ...] = (
    PatchNote(
        slug="mock-patch-1-0-7",
        version="v1.0.7",
        title="최신 Mock 업데이트 샘플",
        summary="UI 검증용 최신 버전 항목입니다. 실제 라이브 패치가 아닙니다.",
        published_at=_D1,
        patch_types=("update",),
        changes=(
            PatchChangeItem("로비 UI 샘플 조정", "레이아웃 밀도 확인용"),
            PatchChangeItem("설정 메뉴 표기 정리", "문구만 예시"),
            PatchChangeItem("알림 배너 스타일 샘플", "시각 검증"),
            PatchChangeItem("로딩 문구 예시", "카피 길이 확인"),
        ),
        keywords=("최신", "로비", "설정"),
        is_featured=True,
        body=(
            _p("이 문서는 CLIPS Patch Timeline용 Mock입니다."),
            _h2("예시 변경점"),
            _ul("로비 UI 샘플 조정", "설정 메뉴 표기 정리", "알림 배너 스타일 샘플"),
            _callout("공식 패치노트처럼 오해하지 마세요."),
            _note("CLIPS Mock · 개발용 데이터"),
        ),
    ),
    PatchNote(
        slug="mock-patch-1-0-6",
        version="v1.0.6",
        title="클래스 밸런스 조정 및 편의 기능 개선 (샘플)",
        summary=(
            "밸런스·업데이트 유형을 동시에 담은 복합 샘플입니다. "
            "수치는 의도적으로 넣지 않았으며, 타임라인 배지 조합 UI를 검증합니다."
        ),
        published_at=_D2,
        patch_types=("update", "balance"),
        changes=(
            PatchChangeItem("샘플 클래스 A 스킬 표기", "밸런스 UI"),
            PatchChangeItem("샘플 클래스 B 쿨다운 문구", "예시만"),
            PatchChangeItem("파티 초대 흐름 샘플", "편의성"),
            PatchChangeItem("퀵슬롯 정렬 예시", "레이아웃"),
            PatchChangeItem("전투 로그 필터 샘플", "가독성"),
            PatchChangeItem("툴팁 줄바꿈 점검", "긴 문구"),
        ),
        keywords=("밸런스", "클래스", "편의"),
        body=(
            _p("복합 유형(업데이트+밸런스) 배지 표시를 확인합니다."),
            _h2("예시 항목"),
            _ul("클래스 표기 샘플", "편의 기능 샘플"),
            _note("수치·확정 밸런스 안내가 아닙니다."),
        ),
    ),
    PatchNote(
        slug="mock-patch-1-0-5",
        version="v1.0.5",
        title="전투·스킬 밸런스 중심 Mock",
        summary="밸런스 필터와 타임라인 강조를 위한 샘플 항목입니다.",
        published_at=_D3,
        patch_types=("balance",),
        changes=(
            PatchChangeItem("원거리 딜 표기 샘플"),
            PatchChangeItem("근접 방어 문구 예시"),
            PatchChangeItem("보스 패턴 설명 정리", "문서용"),
            PatchChangeItem("버프 아이콘 정렬", "UI"),
        ),
        keywords=("전투", "스킬", "밸런스"),
        body=(
            _p("밸런스 중심 Mock입니다. 실제 조정 내역이 아닙니다."),
            _ul("딜 표기 샘플", "방어 문구 예시"),
            _note("CLIPS Mock"),
        ),
    ),
    PatchNote(
        slug="mock-patch-1-0-4",
        version="v1.0.4",
        title="안정성·버그 수정 묶음 (샘플)",
        summary="버그 수정 유형 배지와 짧은 변경 목록을 검증합니다.",
        published_at=_D4,
        patch_types=("bugfix",),
        changes=(
            PatchChangeItem("인벤토리 정렬 오류 재현용 메모"),
            PatchChangeItem("채팅 입력 포커스 샘플"),
            PatchChangeItem("맵 마커 깜빡임 UI 점검"),
        ),
        keywords=("버그", "안정성", "수정"),
        body=(
            _p("버그 수정 중심 샘플입니다. 실제 이슈 트래커와 무관합니다."),
            _ul("인벤토리", "채팅", "맵 마커"),
            _callout("해결 완료처럼 읽히지 않도록 확정 표현을 피했습니다."),
        ),
    ),
    PatchNote(
        slug="mock-patch-1-0-3",
        version="v1.0.3",
        title="시스템·성능·설정 개선 샘플",
        summary="시스템 유형 필터용 Mock입니다. 성능 수치는 넣지 않았습니다.",
        published_at=_D5,
        patch_types=("system",),
        changes=(
            PatchChangeItem("그래픽 옵션 라벨 정리"),
            PatchChangeItem("저장 슬롯 안내 문구"),
            PatchChangeItem("네트워크 재시도 UI 샘플"),
            PatchChangeItem("로그 수집 토글 예시"),
            PatchChangeItem("접근성 고대비 미리보기"),
        ),
        keywords=("시스템", "성능", "설정", "접근성"),
        body=(
            _p("시스템 개선 Mock입니다."),
            _h2("예시"),
            _ul("그래픽 옵션", "저장 슬롯", "네트워크 UI"),
            _note("벤치마크·성능 수치 없음"),
        ),
    ),
    PatchNote(
        slug="mock-patch-1-0-2",
        version="v1.0.2",
        title="시즌 이벤트 연동 UI 샘플",
        summary="이벤트 유형 배지와 따뜻한 강조색을 확인하기 위한 Mock입니다.",
        published_at=_D6,
        patch_types=("event",),
        changes=(
            PatchChangeItem("이벤트 허브 진입 샘플"),
            PatchChangeItem("보상 수령 버튼 레이아웃"),
            PatchChangeItem("기간 표기 형식 예시"),
        ),
        keywords=("이벤트", "시즌", "보상"),
        body=(
            _p("이벤트 관련 Mock입니다. 일정·보상은 가짜입니다."),
            _ul("허브 진입", "보상 버튼", "기간 표기"),
            _note("공식 이벤트 공지가 아닙니다."),
        ),
    ),
    PatchNote(
        slug="mock-patch-1-0-1-long",
        version="v1.0.1",
        title=(
            "긴 제목 검증용 Mock — 패치노트 타임라인에서 여러 줄로 줄바꿈되어도 "
            "버전·배지·상세 링크가 깨지지 않는지 확인하는 샘플 제목입니다"
        ),
        summary=(
            "긴 요약 검증용입니다. 모바일에서 요약이 2~3줄로 잘리고, 데스크톱 타임라인에서 "
            "행 높이가 과도하게 커지지 않는지 확인합니다. 실제 업데이트 내용이 아니며 "
            "CLIPS 개발용 Mock 데이터로만 사용합니다. "
            "키워드 검색(긴요약, 줄바꿈)도 함께 점검합니다."
        ),
        published_at=_D7,
        patch_types=("update", "system", "bugfix"),
        changes=(
            PatchChangeItem("초장문 변경점 제목이 한 줄로 넘칠 때의 줄바꿈 샘플"),
            PatchChangeItem("키워드 검색용 태그 문구", "긴요약"),
            PatchChangeItem("다중 유형 배지 줄바꿈"),
        ),
        keywords=("긴요약", "줄바꿈", "레이아웃", "긴제목"),
        body=(
            _p("긴 제목·요약·다중 유형 케이스입니다."),
            _callout("공식 패치처럼 읽히지 않도록 Mock 표기를 유지합니다."),
            _note("CLIPS Mock"),
        ),
    ),
)


def list_patch_notes() -> tuple[PatchNote, ...]:
    from app.services.demo_content import demo_content_enabled

    if not demo_content_enabled():
        return ()
    return tuple(sorted(PATCH_NOTES, key=lambda item: item.published_at, reverse=True))


def get_patch_by_slug(slug: str) -> PatchNote | None:
    from app.services.demo_content import demo_content_enabled

    if not demo_content_enabled():
        return None
    for item in PATCH_NOTES:
        if item.slug == slug:
            return item
    return None


def parse_patch_filter(raw: str | None) -> PatchFilterKey:
    if raw is None or raw == "" or raw == "all":
        return "all"
    mapping: dict[str, PatchFilterKey] = {
        key: key for key, _ in PATCH_TYPE_FILTERS if key != "all"
    }
    return mapping.get(raw, "all")


def patch_type_labels(types: tuple[PatchType, ...]) -> tuple[str, ...]:
    return tuple(PATCH_TYPE_LABELS[t] for t in types)


def _search_blob(note: PatchNote) -> str:
    parts = [
        note.title,
        note.version,
        note.summary,
        *note.keywords,
        *(change.title for change in note.changes),
        *(change.summary for change in note.changes if change.summary),
        *patch_type_labels(note.patch_types),
    ]
    return " ".join(parts).casefold()


def filter_patch_notes(
    *,
    type_key: PatchFilterKey = "all",
    query: str = "",
) -> tuple[PatchNote, ...]:
    items = list_patch_notes()
    if type_key != "all":
        items = tuple(n for n in items if type_key in n.patch_types)
    q = query.strip().casefold()
    if q:
        items = tuple(n for n in items if q in _search_blob(n))
    return items


def build_patch_list_query(*, type_key: PatchFilterKey, query: str = "") -> str:
    params: dict[str, str] = {}
    if type_key != "all":
        params["type"] = type_key
    q = query.strip()
    if q:
        params["q"] = q
    if not params:
        return "/news/patch-notes"
    return f"/news/patch-notes?{urlencode(params)}"


def patch_filter_tabs(*, query: str = "") -> list[dict[str, str]]:
    tabs: list[dict[str, str]] = []
    for key, label in PATCH_TYPE_FILTERS:
        tabs.append(
            {
                "key": key,
                "label": label,
                "href": build_patch_list_query(type_key=key, query=query),
            }
        )
    return tabs


def patch_note_as_news_item(note: PatchNote) -> NewsItem:
    """Adapt PatchNote for shared news detail / hub consumers."""
    primary = note.patch_types[0] if note.patch_types else "update"
    badge_variant = {
        "update": "update",
        "balance": "update",
        "bugfix": "notice",
        "system": "notice",
        "event": "event",
    }.get(primary, "update")
    return NewsItem(
        slug=note.slug,
        category="patch",
        title=note.title,
        summary=note.summary,
        published_at=note.published_at,
        updated_at=None,
        source_name=note.source_name,
        source_url=note.source_url,
        is_featured=note.is_featured,
        status_label=note.status_label,
        body=note.body,
        badge_label="패치노트",
        badge_variant=badge_variant,
    )


def patch_notes_as_news_items() -> tuple[NewsItem, ...]:
    return tuple(patch_note_as_news_item(n) for n in list_patch_notes())
