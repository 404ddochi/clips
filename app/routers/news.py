"""News hub, category lists, and article detail pages (mock data)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context
from app.services.content_types import (
    CATEGORY_LIST_META,
    MOCK_ROBOTS,
    NEWS_CATEGORY_TABS,
    PAGE_TITLE_SUFFIX,
    NewsCategory,
)
from app.services.news_mock_data import (
    detail_route_for,
    get_featured_news,
    get_latest_by_category,
    get_news_by_slug,
    list_news,
    news_neighbors,
    related_news,
)
from app.services.seo_content import build_article_json_ld, build_breadcrumb_json_ld

router = APIRouter(tags=["news"])


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "news",
        "category_tabs": NEWS_CATEGORY_TABS,
    }


def _list_title(label: str) -> str:
    return f"{label} | {PAGE_TITLE_SUFFIX}"


def _detail_title(document_title: str) -> str:
    return f"{document_title} | CLIPS"


@router.get("/news", response_class=HTMLResponse, name="news")
def news_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    all_items = list_news()
    featured = get_featured_news()
    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "소식", "route_name": "news", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("소식", settings.absolute_url("/news")),
            ],
        ),
    ]
    context = {
        **_layout(request),
        "active_tab": "all",
        "featured": featured,
        "latest_notice": get_latest_by_category("notice"),
        "latest_event": get_latest_by_category("event"),
        "latest_patch": get_latest_by_category("patch"),
        "items": all_items,
        "breadcrumbs": crumbs,
        "detail_route_for": detail_route_for,
        **seo_context(
            title=_list_title("소식"),
            description=(
                "CLIPS Mock 소식 허브입니다. 공지·이벤트·패치노트 UI를 검증하며 "
                "실제 공식 소식이 아닙니다."
            ),
            canonical_url=settings.absolute_url("/news"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "news/index.html", context)


def _render_category_list(request: Request, category: NewsCategory) -> HTMLResponse:
    settings = get_settings()
    meta = CATEGORY_LIST_META[category]
    items = list_news(category=category)
    path = meta["path_prefix"]
    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "소식", "route_name": "news", "current": False},
        {"label": meta["title"], "route_name": meta["route_name"], "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("소식", settings.absolute_url("/news")),
                (meta["title"], settings.absolute_url(path)),
            ],
        ),
    ]
    context = {
        **_layout(request),
        "active_tab": category,
        "list_title": meta["title"],
        "list_description": meta["description"],
        "detail_route": meta["detail_route"],
        "items": items,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_list_title(meta["title"]),
            description=meta["description"],
            canonical_url=settings.absolute_url(path),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "news/list.html", context)


@router.get("/news/notices", response_class=HTMLResponse, name="news_notices")
def news_notices(request: Request) -> HTMLResponse:
    return _render_category_list(request, "notice")


@router.get("/news/events", response_class=HTMLResponse, name="news_events")
def news_events(request: Request) -> HTMLResponse:
    return _render_category_list(request, "event")


@router.get("/news/patch-notes", response_class=HTMLResponse, name="news_patch_notes")
def news_patch_notes(request: Request) -> HTMLResponse:
    return _render_category_list(request, "patch")


def _render_detail(
    request: Request,
    category: NewsCategory,
    slug: str,
) -> HTMLResponse:
    item = get_news_by_slug(category, slug)
    if item is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    meta = CATEGORY_LIST_META[category]
    detail_route = meta["detail_route"]
    page_path = f"{meta['path_prefix']}/{slug}"
    page_url = settings.absolute_url(page_path)
    prev_item, next_item = news_neighbors(category, slug)
    related = related_news(item)

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "소식", "route_name": "news", "current": False},
        {"label": meta["title"], "route_name": meta["route_name"], "current": False},
        {"label": item.title, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("소식", settings.absolute_url("/news")),
                (meta["title"], settings.absolute_url(meta["path_prefix"])),
                (item.title, page_url),
            ],
        ),
        build_article_json_ld(settings, item=item, page_url=page_url),
    ]
    context = {
        **_layout(request),
        "item": item,
        "list_route": meta["route_name"],
        "list_label": meta["title"],
        "detail_route": detail_route,
        "prev_item": prev_item,
        "next_item": next_item,
        "related_items": related,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_detail_title(item.title),
            description=item.summary,
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "news/detail.html", context)


@router.get(
    "/news/notices/{slug}",
    response_class=HTMLResponse,
    name="news_notice_detail",
)
def news_notice_detail(request: Request, slug: str) -> HTMLResponse:
    return _render_detail(request, "notice", slug)


@router.get(
    "/news/events/{slug}",
    response_class=HTMLResponse,
    name="news_event_detail",
)
def news_event_detail(request: Request, slug: str) -> HTMLResponse:
    return _render_detail(request, "event", slug)


@router.get(
    "/news/patch-notes/{slug}",
    response_class=HTMLResponse,
    name="news_patch_detail",
)
def news_patch_detail(request: Request, slug: str) -> HTMLResponse:
    return _render_detail(request, "patch", slug)
