"""Item list and detail pages (publicly disclosed info only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context
from app.services.content_types import ITEM_PENDING_LABEL, ITEM_SHORT_PENDING, MOCK_ROBOTS
from app.services.item_data import (
    filter_items,
    get_item_by_slug,
    has_item_catalogue,
    has_item_category_filters,
    item_category_tabs,
    list_items,
    parse_item_category,
)
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["items"])

_ITEM_PAGE_TITLE = "아이템 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
_ITEM_PAGE_DESCRIPTION = (
    "이클립스: 더 어웨이크닝 공식 아이템 정보가 공개되면 CLIPS에서 업데이트합니다."
)
_ITEM_WAITING_DESCRIPTION = (
    "공식 아이템 정보가 공개되면 업데이트됩니다. CLIPS는 비공식 정보 플랫폼입니다."
)

_UPCOMING_TOPICS = ("등급", "옵션", "획득처", "강화", "제작", "거래 정보")

_RELATED_LINKS = (
    {"label": "클래스", "route_name": "classes"},
    {"label": "보스", "route_name": "bosses"},
    {"label": "쿠폰", "route_name": "coupons"},
    {"label": "홈", "route_name": "home"},
)


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "items",
    }


@router.get("/items", response_class=HTMLResponse, name="items")
def items_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    catalogue_ready = has_item_catalogue()
    category = parse_item_category(request.query_params.get("category"))
    query = (request.query_params.get("q") or "").strip()

    if catalogue_ready:
        items = filter_items(category=category, query=query)
        category_tabs = item_category_tabs(query=query)
        show_filters = has_item_category_filters()
    else:
        items = list_items()
        category_tabs = []
        show_filters = False
        category = "all"
        query = ""

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "아이템", "route_name": "items", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("아이템", settings.absolute_url("/items")),
            ],
        ),
    ]
    description = (
        _ITEM_PAGE_DESCRIPTION if catalogue_ready else _ITEM_WAITING_DESCRIPTION
    )
    context = {
        **_layout(request),
        "items": items,
        "item_count": len(items),
        "catalogue_ready": catalogue_ready,
        "current_category": category,
        "search_query": query,
        "category_tabs": category_tabs,
        "show_filters": show_filters,
        "pending_label": ITEM_PENDING_LABEL,
        "short_pending": ITEM_SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "related_links": _RELATED_LINKS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_ITEM_PAGE_TITLE,
            description=description,
            canonical_url=settings.absolute_url("/items"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "items/index.html", context)


@router.get("/items/{slug}", response_class=HTMLResponse, name="item_detail")
def item_detail(request: Request, slug: str) -> HTMLResponse:
    item = get_item_by_slug(slug)
    if item is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    page_path = f"/items/{slug}"
    page_url = settings.absolute_url(page_path)
    others = [i for i in list_items() if i.slug != slug]

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "아이템", "route_name": "items", "current": False},
        {"label": item.name, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("아이템", settings.absolute_url("/items")),
                (item.name, page_url),
            ],
        ),
    ]

    info_cards: list[dict[str, str]] = []
    if item.category and not item.category_pending:
        info_cards.append({"title": "분류", "body": item.category})
    if item.slot_or_purpose and not item.slot_pending:
        info_cards.append({"title": "부위·목적", "body": item.slot_or_purpose})
    if item.acquisition and not item.acquisition_pending:
        info_cards.append({"title": "획득", "body": item.acquisition})

    summary_display = (
        ITEM_PENDING_LABEL
        if item.summary_pending or not item.summary
        else item.summary
    )

    context = {
        **_layout(request),
        "item": item,
        "related_items": others,
        "info_cards": info_cards,
        "summary_display": summary_display,
        "pending_label": ITEM_PENDING_LABEL,
        "short_pending": ITEM_SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=f"{item.name} - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트",
            description=item.summary or _ITEM_WAITING_DESCRIPTION,
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "items/detail.html", context)
