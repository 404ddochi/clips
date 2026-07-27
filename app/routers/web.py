"""Public web pages (SSR)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import (
    DEFAULT_HOME_DESCRIPTION,
    DEFAULT_HOME_TITLE,
    INFO_MENU_CARDS,
    MAIN_NAV,
    PLACEHOLDER_NEWS,
    PREPARING_SECTIONS,
)
from app.dependencies import get_templates, seo_context
from app.services.seo import build_home_json_ld, build_website_json_ld

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request) -> HTMLResponse:
    settings = get_settings()
    structured = [
        build_website_json_ld(settings),
        build_home_json_ld(settings),
    ]
    context = {
        "request": request,
        "nav_items": MAIN_NAV,
        "news_cards": PLACEHOLDER_NEWS,
        "info_cards": INFO_MENU_CARDS,
        "active_nav": "home",
        **seo_context(
            title=DEFAULT_HOME_TITLE,
            description=DEFAULT_HOME_DESCRIPTION,
            canonical_url=settings.absolute_url("/"),
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "home.html", context)


def _preparing_page(request: Request, section_key: str) -> HTMLResponse:
    settings = get_settings()
    label = PREPARING_SECTIONS.get(section_key, "페이지")
    title = f"{label} - 클립스"
    description = (
        f"클립스 {label} 페이지는 준비 중입니다. "
        "이클립스: 더 어웨이크닝 비공식 정보를 순차적으로 제공할 예정입니다."
    )
    path = next((item.path for item in MAIN_NAV if item.key == section_key), f"/{section_key}")

    context = {
        "request": request,
        "nav_items": MAIN_NAV,
        "section_label": label,
        "active_nav": section_key,
        **seo_context(
            title=title,
            description=description,
            canonical_url=settings.absolute_url(path),
            robots="noindex, follow",
        ),
    }
    return get_templates().TemplateResponse(request, "preparing.html", context)


@router.get("/news", response_class=HTMLResponse, name="news")
def news_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "news")


@router.get("/classes", response_class=HTMLResponse, name="classes")
def classes_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "classes")


@router.get("/contents", response_class=HTMLResponse, name="contents")
def contents_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "contents")


@router.get("/items", response_class=HTMLResponse, name="items")
def items_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "items")


@router.get("/bosses", response_class=HTMLResponse, name="bosses")
def bosses_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "bosses")


@router.get("/maps", response_class=HTMLResponse, name="maps")
def maps_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "maps")


@router.get("/guides", response_class=HTMLResponse, name="guides")
def guides_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "guides")


@router.get("/coupons", response_class=HTMLResponse, name="coupons")
def coupons_preparing(request: Request) -> HTMLResponse:
    return _preparing_page(request, "coupons")
