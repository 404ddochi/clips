"""Public web pages (SSR)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import (
    DEFAULT_HOME_DESCRIPTION,
    DEFAULT_HOME_TITLE,
    MAIN_NAV,
    NOINDEX_ROBOTS,
    PAGE_DESCRIPTIONS,
    page_title,
)
from app.dependencies import get_templates, seo_context
from app.services.coming_soon_data import get_coming_soon_page
from app.services.home_page_data import build_home_page_data
from app.services.seo_content import build_breadcrumb_json_ld
from app.services.structured_data import build_home_structured_data

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
    context = {
        **_base_layout_context(request, "home"),
        "home": build_home_page_data(),
        **seo_context(
            title=DEFAULT_HOME_TITLE,
            description=DEFAULT_HOME_DESCRIPTION,
            canonical_url=settings.canonical_url("/"),
            structured_data=build_home_structured_data(settings),
        ),
    }
    return get_templates().TemplateResponse(request, "home.html", context)


def _render_coming_soon(request: Request, section_key: str) -> HTMLResponse:
    page = get_coming_soon_page(section_key)
    if page is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    if section_key == "contents":
        seo_title = page_title("콘텐츠")
        seo_description = PAGE_DESCRIPTIONS["contents"]
        robots = "index, follow"
        structured = [
            build_breadcrumb_json_ld(
                settings,
                [
                    ("홈", settings.canonical_url("/")),
                    ("콘텐츠", settings.canonical_url("/contents")),
                ],
            ),
        ]
    else:
        seo_title = page_title(page.page_title)
        seo_description = (
            f"CLIPS {page.label} 페이지는 준비 중입니다. {page.page_description}"
        )
        robots = NOINDEX_ROBOTS
        structured = []
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
            canonical_url=settings.canonical_url(f"/{section_key}"),
            robots=robots,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "coming_soon.html", context)


@router.get("/contents", response_class=HTMLResponse, name="contents")
def contents_preparing(request: Request) -> HTMLResponse:
    return _render_coming_soon(request, "contents")
