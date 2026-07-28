"""Coupon list and detail pages (mock demo codes only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV, PAGE_DESCRIPTIONS, detail_title, page_title
from app.dependencies import get_templates, seo_context
from app.services.content_types import COUPON_STATUS_FILTERS, MOCK_ROBOTS
from app.services.coupon_mock_data import (
    filter_coupons,
    get_coupon_by_slug,
    list_coupons,
    parse_coupon_filter,
)
from app.services.seo import meta_description
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["coupons"])

_COUPON_PAGE_TITLE = page_title("쿠폰")
_COUPON_PAGE_DESCRIPTION = PAGE_DESCRIPTIONS["coupons"]

_USAGE_STEPS = (
    "상태 필터로 원하는 쿠폰을 좁힙니다.",
    "코드를 확인한 뒤 「코드 복사」를 누릅니다.",
    "게임 내 쿠폰 입력처에서 코드를 사용하세요.",
)

_USAGE_STEPS_DEMO = (
    "상태 필터로 원하는 쿠폰을 좁힙니다.",
    "코드를 확인한 뒤 「코드 복사」를 누릅니다.",
    "표시된 코드는 Mock 데모이며 게임에서 교환되지 않을 수 있습니다.",
)

_WARNINGS = (
    "쿠폰 유효 기간과 교환 가능 여부는 공식 안내를 기준으로 확인하세요.",
    "CLIPS는 비공식 정보 플랫폼입니다.",
)

_WARNINGS_DEMO = (
    "SAMPLE·CLIPS-DEMO 계열 코드는 UI 검증용입니다.",
    "실제 사용 가능한 공식 쿠폰처럼 오해하지 마세요.",
    "CLIPS는 비공식 정보 플랫폼입니다.",
)

# Expired rows keep a visible disabled copy control so the primary action
# remains discoverable and screen readers can announce why copy is unavailable.
_EXPIRED_COPY_POLICY = "disabled"


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "coupons",
    }


def _status_filters() -> list[dict[str, str]]:
    filters: list[dict[str, str]] = []
    for key, label in COUPON_STATUS_FILTERS:
        href = "/coupons" if key == "all" else f"/coupons?status={key}"
        filters.append({"key": key, "label": label, "href": href})
    return filters


@router.get("/coupons", response_class=HTMLResponse, name="coupons")
def coupons_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    raw_status = request.query_params.get("status")
    current_status = parse_coupon_filter(raw_status)
    # Mock source is the COUPON_ITEMS tuple (not a callable). Always use its length / filter helper.
    coupons = filter_coupons(current_status)
    coupon_count = len(coupons)
    status_filters = _status_filters()
    is_mock = settings.allows_demo_content()

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "쿠폰", "route_name": "coupons", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("쿠폰", settings.absolute_url("/coupons")),
            ],
        ),
    ]

    context: dict[str, object] = {
        **_layout(request),
        "coupons": coupons,
        "coupon_count": coupon_count,
        "current_status": current_status,
        "status_filters": status_filters,
        "is_mock": is_mock,
        "usage_steps": _USAGE_STEPS_DEMO if is_mock else _USAGE_STEPS,
        "warnings": _WARNINGS_DEMO if is_mock else _WARNINGS,
        "expired_copy_policy": _EXPIRED_COPY_POLICY,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_COUPON_PAGE_TITLE,
            description=_COUPON_PAGE_DESCRIPTION,
            canonical_url=settings.absolute_url("/coupons"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }

    return get_templates().TemplateResponse(request, "coupons/index.html", context)


@router.get("/coupons/{slug}", response_class=HTMLResponse, name="coupon_detail")
def coupon_detail(request: Request, slug: str) -> HTMLResponse:
    item = get_coupon_by_slug(slug)
    if item is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    is_mock = settings.allows_demo_content()
    page_path = f"/coupons/{slug}"
    page_url = settings.absolute_url(page_path)
    others = [c for c in list_coupons() if c.slug != slug][:3]
    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "쿠폰", "route_name": "coupons", "current": False},
        {"label": item.title, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("쿠폰", settings.absolute_url("/coupons")),
                (item.title, page_url),
            ],
        ),
    ]
    context = {
        **_layout(request),
        "item": item,
        "related_coupons": others,
        "is_mock": is_mock,
        "usage_steps": _USAGE_STEPS_DEMO if is_mock else _USAGE_STEPS,
        "warnings": _WARNINGS_DEMO if is_mock else _WARNINGS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=detail_title(item.title),
            description=meta_description(item.reward_summary, fallback=_COUPON_PAGE_DESCRIPTION),
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "coupons/detail.html", context)
