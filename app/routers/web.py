"""Public web pages (SSR)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import DEFAULT_HOME_DESCRIPTION, DEFAULT_HOME_TITLE, MAIN_NAV
from app.dependencies import get_templates, seo_context
from app.services.coming_soon_data import get_coming_soon_page
from app.services.home_page_data import (
    ARCHIVE_TEASERS,
    PLATFORM_FEATURES,
    QUICK_LINKS,
    build_home_info_strip,
    build_home_news_items,
)
from app.services.seo import build_home_json_ld, build_website_json_ld

router = APIRouter(tags=["web"])


def _base_layout_context(request: Request, active_menu: str) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": active_menu,
    }


@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request) -> HTMLResponse:
    settings = get_settings()
    structured = [
        build_website_json_ld(settings),
        build_home_json_ld(settings),
    ]
    context = {
        **_base_layout_context(request, "home"),
        "quick_links": QUICK_LINKS,
        "news_items": build_home_news_items(),
        "platform_features": PLATFORM_FEATURES,
        "archive_teasers": ARCHIVE_TEASERS,
        "info_strip": build_home_info_strip(),
        **seo_context(
            title=DEFAULT_HOME_TITLE,
            description=DEFAULT_HOME_DESCRIPTION,
            canonical_url=settings.absolute_url("/"),
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "home.html", context)


def _render_coming_soon(request: Request, section_key: str) -> HTMLResponse:
    page = get_coming_soon_page(section_key)
    if page is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    seo_title = f"{page.page_title} - 클립스"
    seo_description = f"클립스 {page.label} 페이지는 준비 중입니다. {page.page_description}"
    context = {
        **_base_layout_context(request, section_key),
        "page": page,
        "breadcrumbs": (
            {"label": "홈", "route_name": "home", "current": False},
            {"label": page.label, "route_name": page.route_name, "current": True},
        ),
        **seo_context(
            title=seo_title,
            description=seo_description,
            canonical_url=settings.absolute_url(request.url.path),
            robots="noindex, follow",
        ),
    }
    return get_templates().TemplateResponse(request, "coming_soon.html", context)


@router.get("/contents", response_class=HTMLResponse, name="contents")
def contents_preparing(request: Request) -> HTMLResponse:
    return _render_coming_soon(request, "contents")



@router.get("/guides", response_class=HTMLResponse, name="guides")
def guides_preparing(request: Request) -> HTMLResponse:
    return _render_coming_soon(request, "guides")
