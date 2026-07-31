"""Shared HTML/plain error page responses for handlers and middleware."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context

ERROR_PAGE_SHORTCUTS: tuple[dict[str, str], ...] = (
    {"label": "홈", "route_name": "home", "icon": "home"},
    {"label": "소식", "route_name": "news", "icon": "news"},
    {"label": "클래스", "route_name": "classes", "icon": "class"},
    {"label": "아이템", "route_name": "items", "icon": "item"},
    {"label": "보스", "route_name": "bosses", "icon": "boss"},
    {"label": "지도", "route_name": "maps", "icon": "map"},
    {"label": "공략", "route_name": "guides", "icon": "guide"},
    {"label": "쿠폰", "route_name": "coupons", "icon": "coupon"},
)


def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept or "*/*" in accept or not accept


def not_found_response(request: Request) -> HTMLResponse:
    """Branded 404 for HTML clients; plain Not Found otherwise."""
    if wants_html(request):
        return get_templates().TemplateResponse(
            request,
            "errors/404.html",
            {
                "request": request,
                "status_code": 404,
                "nav_items": MAIN_NAV,
                "active_menu": "",
                "shortcut_links": ERROR_PAGE_SHORTCUTS,
                **seo_context(
                    title="페이지를 찾을 수 없습니다 - CLIPS",
                    description=(
                        "입력한 주소가 변경되었거나 존재하지 않는 페이지입니다. "
                        "CLIPS 메뉴에서 원하는 정보를 다시 찾아보세요."
                    ),
                    canonical_url=None,
                    robots="noindex, nofollow",
                ),
            },
            status_code=404,
        )
    return HTMLResponse(content="Not Found", status_code=404)


def server_error_response(request: Request) -> HTMLResponse:
    """Branded 500 for HTML clients; plain Internal Server Error otherwise."""
    if wants_html(request):
        return get_templates().TemplateResponse(
            request,
            "errors/500.html",
            {
                "request": request,
                "status_code": 500,
                "nav_items": MAIN_NAV,
                "active_menu": "",
                "shortcut_links": ERROR_PAGE_SHORTCUTS,
                **seo_context(
                    title="일시적인 오류가 발생했습니다 - CLIPS",
                    description=(
                        "요청을 처리하는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."
                    ),
                    canonical_url=None,
                    robots="noindex, nofollow",
                ),
            },
            status_code=500,
        )
    return HTMLResponse(content="Internal Server Error", status_code=500)
