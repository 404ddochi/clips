"""Unified search page."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV, page_title
from app.dependencies import get_templates, seo_context
from app.services.search import (
    MAX_QUERY_LENGTH,
    SearchResponse,
    normalize_search_query,
    resolve_type_filter,
    search_all,
    search_filter_tabs,
)
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["search"])

_SEARCH_IDLE_DESCRIPTION = (
    "CLIPS에서 이클립스: 더 어웨이크닝의 소식, 클래스, 아이템, 보스, 지도와 "
    "공략을 통합 검색하세요."
)


@router.get("/search", response_class=HTMLResponse, name="search")
def search_page(request: Request) -> HTMLResponse:
    settings = get_settings()
    raw_q = request.query_params.get("q")
    type_filter = resolve_type_filter(request.query_params.get("type"))
    normalized = normalize_search_query(raw_q)
    display_query = normalized.normalized

    if normalized.error:
        search_response = SearchResponse(
            query=display_query,
            groups=(),
            total_count=0,
            displayed_count=0,
            searched_types=(),
            type_filter=type_filter,
            error=normalized.error,
        )
        form_query = display_query[:MAX_QUERY_LENGTH]
        has_active_search = False
        seo_title = page_title("통합 검색")
        seo_description = _SEARCH_IDLE_DESCRIPTION
        tab_query = ""
    elif normalized.should_search:
        search_response = search_all(display_query, type_filter=type_filter)
        form_query = display_query
        has_active_search = True
        seo_title = page_title(f"{display_query} 검색 결과")
        seo_description = (
            f"CLIPS에서 ‘{display_query}’와 관련된 이클립스: 더 어웨이크닝 "
            "정보를 검색한 결과입니다."
        )
        tab_query = display_query
    else:
        search_response = SearchResponse(
            query="",
            groups=(),
            total_count=0,
            displayed_count=0,
            searched_types=(),
            type_filter=type_filter,
        )
        form_query = ""
        has_active_search = False
        seo_title = page_title("통합 검색")
        seo_description = _SEARCH_IDLE_DESCRIPTION
        tab_query = ""

    canonical = settings.canonical_url("/search")
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.canonical_url("/")),
                ("통합 검색", canonical),
            ],
        ),
    ]

    context = {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "",
        "search_response": search_response,
        "search_query": form_query,
        "type_filter": type_filter,
        "filter_tabs": search_filter_tabs(query=tab_query, type_filter=type_filter),
        "max_query_length": MAX_QUERY_LENGTH,
        "has_active_search": has_active_search,
        "validation_error": normalized.error,
        "breadcrumbs": (
            {"label": "홈", "route_name": "home", "current": False},
            {"label": "통합 검색", "route_name": "search", "current": True},
        ),
        **seo_context(
            title=seo_title,
            description=seo_description,
            canonical_url=canonical,
            og_url=canonical,
            robots="noindex, follow",
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "search/index.html", context)
