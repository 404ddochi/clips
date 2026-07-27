"""Development-only routes (CDL showcase)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context

router = APIRouter(prefix="/dev", tags=["dev"])

CDL_ICON_NAMES: tuple[str, ...] = (
    "home",
    "notice",
    "event",
    "patch",
    "coupon",
    "class",
    "content",
    "item",
    "boss",
    "map",
    "guide",
    "update",
    "search",
    "menu",
    "close",
    "arrow-right",
    "external",
    "clock",
    "tag",
    "filter",
    "chevron-down",
    "check",
    "warning",
    "info",
    "theme-system",
    "theme-light",
    "theme-dark",
)


@router.get("/design-system", response_class=HTMLResponse, name="design_system")
def design_system(request: Request) -> HTMLResponse:
    settings = get_settings()
    if not settings.is_design_system_enabled():
        raise HTTPException(status_code=404)

    context = {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "",
        "cdl_icons": CDL_ICON_NAMES,
        **seo_context(
            title="CLIPS Design Language (개발용) - 클립스",
            description=(
                "CLIPS Design Language 컴포넌트 쇼케이스. 개발 환경 전용 샘플 페이지입니다."
            ),
            canonical_url=settings.absolute_url("/dev/design-system"),
            robots="noindex, nofollow",
        ),
    }
    return get_templates().TemplateResponse(request, "dev/design_system.html", context)
