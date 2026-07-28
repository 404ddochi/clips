"""Mock coupon data (demo codes only — not real redeemable codes)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.content_types import (
    COUPON_STATUS_LABELS,
    ArticleBlock,
    CouponFilterKey,
    CouponItem,
    CouponStatus,
)

_FROM = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
_FROM_LATE = datetime(2026, 7, 10, 0, 0, tzinfo=UTC)
_UNTIL_OK = datetime(2026, 8, 31, 23, 59, tzinfo=UTC)
_UNTIL_OK2 = datetime(2026, 9, 15, 23, 59, tzinfo=UTC)
_UNTIL_OK3 = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)
_UNTIL_SOON = datetime(2026, 7, 28, 23, 59, tzinfo=UTC)
_UNTIL_GONE = datetime(2026, 6, 30, 23, 59, tzinfo=UTC)
_UNTIL_GONE2 = datetime(2026, 5, 31, 23, 59, tzinfo=UTC)


def _p(text: str) -> ArticleBlock:
    return ArticleBlock(kind="paragraph", text=text)


def _note(text: str) -> ArticleBlock:
    return ArticleBlock(kind="note", text=text)


def _callout(text: str) -> ArticleBlock:
    return ArticleBlock(kind="callout", text=text)


# All codes are intentionally fake / sample-shaped. Not redeemable in-game.
COUPON_ITEMS: tuple[CouponItem, ...] = (
    CouponItem(
        slug="sample-available-demo",
        code="SAMPLE-COUPON",
        title="기본 사용 가능 샘플",
        reward_summary="골드 상자 Mock",
        valid_from=_FROM,
        valid_until=_UNTIL_OK,
        status="available",
        status_label=COUPON_STATUS_LABELS["available"],
        source_name="CLIPS Mock",
        source_url=None,
        body=(_p("데모 코드입니다. 실제 교환되지 않습니다."),),
        usage_notes=("Mock 전용",),
    ),
    CouponItem(
        slug="clips-demo-available",
        code="CLIPS-DEMO",
        title="짧은 보상 문구 샘플",
        reward_summary="포션 ×3 (샘플)",
        valid_from=_FROM,
        valid_until=_UNTIL_OK2,
        status="available",
        status_label=COUPON_STATUS_LABELS["available"],
        source_name=None,
        source_url=None,
        body=(_note("출처 없는 행 UI 검증용."),),
        usage_notes=("출처 없음 샘플",),
    ),
    CouponItem(
        slug="clips-welcome-layout",
        code="CLIPS-WELCOME-LAYOUT",
        title="보상 문구가 긴 샘플",
        reward_summary=(
            "레이아웃 검증용 긴 보상 요약입니다. 한 줄 이상일 때도 Coupon Row가 "
            "깨지지 않는지 확인하며, 실제 지급 보상과는 무관합니다."
        ),
        valid_from=_FROM_LATE,
        valid_until=_UNTIL_OK3,
        status="available",
        status_label=COUPON_STATUS_LABELS["available"],
        source_name="CLIPS Mock",
        source_url=None,
        body=(_p("긴 보상 텍스트·고밀도 리스트 검증용 Mock입니다."),),
        usage_notes=("데모만 해당",),
    ),
    CouponItem(
        slug="clips-long-code-sample",
        code="CLIPS-DEMO-LONG-CODE-STRUCTURE-2026",
        title="긴 코드 줄바꿈 샘플",
        reward_summary="경험치 부스트 (샘플)",
        valid_from=_FROM,
        valid_until=_UNTIL_OK,
        status="available",
        status_label=COUPON_STATUS_LABELS["available"],
        source_name="샘플 출처 표기",
        source_url=None,
        body=(_callout("긴 코드 overflow·줄바꿈 확인용입니다."),),
        usage_notes=("코드 길이 스트레스 테스트",),
    ),
    CouponItem(
        slug="clips-demo-expiring",
        code="CLIPS-EXPIRE-SOON",
        title="만료 임박 상태 샘플",
        reward_summary="만료 임박 배지·강조 UI 검증",
        valid_from=_FROM,
        valid_until=_UNTIL_SOON,
        status="expiring",
        status_label=COUPON_STATUS_LABELS["expiring"],
        source_name="CLIPS Mock",
        source_url=None,
        body=(_p("만료 임박 스타일 전용 Mock입니다."),),
        usage_notes=("실제 일정 아님",),
    ),
    CouponItem(
        slug="preparing-expired-sample",
        code="CLIPS-ENDED",
        title="종료된 쿠폰 샘플",
        reward_summary="종료 행 대비·복사 비활성 검증",
        valid_from=_FROM,
        valid_until=_UNTIL_GONE,
        status="expired",
        status_label=COUPON_STATUS_LABELS["expired"],
        source_name=None,
        source_url=None,
        body=(_note("종료 쿠폰은 복사 버튼을 비활성한다(숨기지 않음)."),),
        usage_notes=("만료 Mock",),
    ),
    CouponItem(
        slug="clips-archived-sample",
        code="준비 중",
        title="종료·플레이스홀더 코드 샘플",
        reward_summary="플레이스홀더 코드 표기",
        valid_from=_FROM,
        valid_until=_UNTIL_GONE2,
        status="expired",
        status_label=COUPON_STATUS_LABELS["expired"],
        source_name="CLIPS Mock",
        source_url=None,
        body=(_p("코드 값 '준비 중'은 플레이스홀더입니다."),),
        usage_notes=("입력 금지",),
    ),
)


def list_coupons(*, status: CouponStatus | None = None) -> tuple[CouponItem, ...]:
    from app.services.demo_content import demo_content_enabled

    if not demo_content_enabled():
        return ()
    items = COUPON_ITEMS
    if status is not None:
        items = tuple(item for item in items if item.status == status)
    return items


def filter_coupons(filter_key: CouponFilterKey) -> tuple[CouponItem, ...]:
    if filter_key == "all":
        return list_coupons()
    return list_coupons(status=filter_key)


def parse_coupon_filter(raw: str | None) -> CouponFilterKey:
    mapping: dict[str, CouponFilterKey] = {
        "all": "all",
        "available": "available",
        "expiring": "expiring",
        "expired": "expired",
    }
    if raw is None:
        return "all"
    return mapping.get(raw, "all")


def get_coupon_by_slug(slug: str) -> CouponItem | None:
    from app.services.demo_content import demo_content_enabled

    if not demo_content_enabled():
        return None
    for item in COUPON_ITEMS:
        if item.slug == slug:
            return item
    return None


def coupons_grouped() -> dict[str, tuple[CouponItem, ...]]:
    return {
        "available": list_coupons(status="available"),
        "expiring": list_coupons(status="expiring"),
        "expired": list_coupons(status="expired"),
    }
