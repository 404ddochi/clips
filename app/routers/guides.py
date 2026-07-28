"""Guides hub — CLIPS editorial guide list and detail."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context
from app.services.content_types import GUIDE_UNOFFICIAL_NOTICE, MOCK_ROBOTS
from app.services.guide_data import (
    featured_guides,
    filter_guides,
    get_guide_by_slug,
    guide_category_tabs,
    has_guide_catalogue,
    has_guide_category_filters,
    parse_guide_category,
    related_guides,
    section_anchor_id,
)
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["guides"])

_GUIDE_PAGE_TITLE = "공략 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
_GUIDE_PAGE_DESCRIPTION = (
    "CLIPS가 직접 정리한 이클립스: 더 어웨이크닝 비공식 가이드와 공략을 확인하세요."
)
_GUIDE_WAITING_DESCRIPTION = (
    "CLIPS 공략을 준비하고 있습니다. "
    "확인된 내용만 순차적으로 등록합니다. CLIPS는 비공식 정보 플랫폼입니다."
)

_PREP_TOPICS = ("입문", "성장", "클래스", "콘텐츠", "시스템", "탐험")

_RELATED_LINKS = (
    {"label": "클래스", "route_name": "classes"},
    {"label": "보스", "route_name": "bosses"},
    {"label": "아이템", "route_name": "items"},
    {"label": "지도", "route_name": "maps"},
    {"label": "홈", "route_name": "home"},
)


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "guides",
    }


@router.get("/guides", response_class=HTMLResponse, name="guides")
def guides_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    catalogue_ready = has_guide_catalogue()
    category = parse_guide_category(request.query_params.get("category"))
    query = (request.query_params.get("q") or "").strip()

    if catalogue_ready:
        guides = filter_guides(category=category, query=query)
        category_tabs = guide_category_tabs(query=query)
        show_filters = has_guide_category_filters()
        featured = featured_guides() if not query and category == "all" else ()
    else:
        guides = ()
        category_tabs = []
        show_filters = False
        category = "all"
        query = ""
        featured = ()

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "공략", "route_name": "guides", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("공략", settings.absolute_url("/guides")),
            ],
        ),
    ]
    description = (
        _GUIDE_PAGE_DESCRIPTION if catalogue_ready else _GUIDE_WAITING_DESCRIPTION
    )
    context = {
        **_layout(request),
        "guides": guides,
        "guide_count": len(guides),
        "catalogue_ready": catalogue_ready,
        "current_category": category,
        "search_query": query,
        "category_tabs": category_tabs,
        "show_filters": show_filters,
        "featured_guides": featured,
        "prep_topics": _PREP_TOPICS,
        "related_links": _RELATED_LINKS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_GUIDE_PAGE_TITLE,
            description=description,
            canonical_url=settings.absolute_url("/guides"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "guides/index.html", context)


@router.get("/guides/{slug}", response_class=HTMLResponse, name="guide_detail")
def guide_detail(request: Request, slug: str) -> HTMLResponse:
    guide = get_guide_by_slug(slug)
    if guide is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    page_path = f"/guides/{slug}"
    page_url = settings.absolute_url(page_path)
    related = related_guides(guide)

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "공략", "route_name": "guides", "current": False},
        {"label": guide.title, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("공략", settings.absolute_url("/guides")),
                (guide.title, page_url),
            ],
        ),
    ]

    toc = [
        {
            "heading": section.heading,
            "anchor": section_anchor_id(section.heading, index),
        }
        for index, section in enumerate(guide.sections)
        if section.heading
    ]

    context = {
        **_layout(request),
        "guide": guide,
        "related_guides": related,
        "toc": toc,
        "show_toc": len(toc) >= 2,
        "unofficial_notice": GUIDE_UNOFFICIAL_NOTICE,
        "section_anchor_id": section_anchor_id,
        "breadcrumbs": crumbs,
        **seo_context(
            title=f"{guide.title} - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트",
            description=guide.summary or _GUIDE_WAITING_DESCRIPTION,
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "guides/detail.html", context)
