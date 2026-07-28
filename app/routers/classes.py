"""Class list and detail pages (publicly disclosed info only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context
from app.services.class_data import (
    class_filter_tabs,
    class_style_labels,
    display_or_pending,
    filter_classes,
    get_class_by_slug,
    list_classes,
    parse_class_filter,
)
from app.services.content_types import CLASS_PENDING_LABEL, CLASS_STYLE_LABELS, MOCK_ROBOTS
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["classes"])

_CLASS_PAGE_TITLE = "클래스 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
_CLASS_PAGE_DESCRIPTION = (
    "이클립스: 더 어웨이크닝 공개 클래스를 비교하고, 무기와 전투 스타일 정보를 "
    "빠르게 확인해 보세요."
)

_UPCOMING_TOPICS = ("스킬", "빌드", "추천 세팅", "전직")
_SHORT_PENDING = "공개 예정"


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "classes",
    }


@router.get("/classes", response_class=HTMLResponse, name="classes")
def classes_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    current_style = parse_class_filter(request.query_params.get("style"))
    classes = filter_classes(style=current_style)
    style_filters = class_filter_tabs()

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "클래스", "route_name": "classes", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("클래스", settings.absolute_url("/classes")),
            ],
        ),
    ]
    context = {
        **_layout(request),
        "classes": classes,
        "class_count": len(classes),
        "current_style": current_style,
        "style_filters": style_filters,
        "style_labels": CLASS_STYLE_LABELS,
        "pending_label": CLASS_PENDING_LABEL,
        "short_pending": _SHORT_PENDING,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_CLASS_PAGE_TITLE,
            description=_CLASS_PAGE_DESCRIPTION,
            canonical_url=settings.absolute_url("/classes"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "classes/index.html", context)


@router.get("/classes/{slug}", response_class=HTMLResponse, name="class_detail")
def class_detail(request: Request, slug: str) -> HTMLResponse:
    item = get_class_by_slug(slug)
    if item is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    page_path = f"/classes/{slug}"
    page_url = settings.absolute_url(page_path)
    others = [c for c in list_classes() if c.slug != slug]

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "클래스", "route_name": "classes", "current": False},
        {"label": item.name, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("클래스", settings.absolute_url("/classes")),
                (item.name, page_url),
            ],
        ),
    ]
    context = {
        **_layout(request),
        "item": item,
        "related_classes": others,
        "style_labels": class_style_labels(item.styles),
        "weapons_display": display_or_pending(
            item.weapons,
            pending=item.weapons_pending,
        ),
        "combat_display": display_or_pending(
            item.combat_styles,
            pending=item.combat_styles_pending,
        ),
        "summary_display": (
            CLASS_PENDING_LABEL if item.summary_pending or not item.summary else item.summary
        ),
        "pending_label": CLASS_PENDING_LABEL,
        "short_pending": _SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=f"{item.name} - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트",
            description=item.summary or _CLASS_PAGE_DESCRIPTION,
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "classes/detail.html", context)
