"""News hub, category lists, and article detail pages (mock data)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV, PAGE_DESCRIPTIONS, detail_title, page_title
from app.dependencies import get_templates, seo_context
from app.services.content_types import (
    CATEGORY_LIST_META,
    MOCK_ROBOTS,
    NEWS_CATEGORY_TABS,
    PATCH_TYPE_LABELS,
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
from app.services.patch_mock_data import (
    build_patch_list_query,
    filter_patch_notes,
    parse_patch_filter,
    patch_filter_tabs,
)
from app.services.seo import meta_description
from app.services.seo_content import build_article_json_ld, build_breadcrumb_json_ld

router = APIRouter(tags=["news"])

_PATCH_PAGE_TITLE = page_title("패치노트")
_PATCH_PAGE_DESCRIPTION = PAGE_DESCRIPTIONS["patch_notes"]
_NEWS_PAGE_DESCRIPTION = PAGE_DESCRIPTIONS["news"]


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "news",
        "category_tabs": NEWS_CATEGORY_TABS,
    }


def _list_title(label: str) -> str:
    return page_title(label)


def _detail_page_title(document_title: str) -> str:
    return detail_title(document_title)


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
            description=_NEWS_PAGE_DESCRIPTION,
            canonical_url=settings.canonical_url("/news"),
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
            description=_NEWS_PAGE_DESCRIPTION,
            canonical_url=settings.canonical_url(path),
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
    settings = get_settings()
    raw_type = request.query_params.get("type")
    current_type = parse_patch_filter(raw_type)
    query = (request.query_params.get("q") or "").strip()
    patches = filter_patch_notes(type_key=current_type, query=query)
    patch_count = len(patches)
    type_filters = patch_filter_tabs(query=query)
    clear_href = build_patch_list_query(type_key="all", query="")
    path = "/news/patch-notes"

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "소식", "route_name": "news", "current": False},
        {"label": "패치노트", "route_name": "news_patch_notes", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("소식", settings.absolute_url("/news")),
                ("패치노트", settings.absolute_url(path)),
            ],
        ),
    ]
    context = {
        **_layout(request),
        "active_tab": "patch",
        "patches": patches,
        "patch_count": patch_count,
        "current_type": current_type,
        "type_filters": type_filters,
        "search_query": query,
        "clear_href": clear_href,
        "patch_type_labels": PATCH_TYPE_LABELS,
        "is_mock": True,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_PATCH_PAGE_TITLE,
            description=_PATCH_PAGE_DESCRIPTION,
            canonical_url=settings.canonical_url(path),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(
        request,
        "news/patch_notes.html",
        context,
    )


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
    fallback_desc = (
        _PATCH_PAGE_DESCRIPTION if category == "patch" else _NEWS_PAGE_DESCRIPTION
    )
    description = meta_description(item.summary, fallback=fallback_desc)
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
        build_article_json_ld(
            settings,
            item=item,
            page_url=page_url,
            description=description,
        ),
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
            title=_detail_page_title(item.title),
            description=description,
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            og_type="article",
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
