"""Map hub — region list and detail (publicly disclosed info only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV, PAGE_DESCRIPTIONS, detail_title, page_title
from app.dependencies import get_templates, seo_context
from app.services.content_types import MAP_PENDING_LABEL, MAP_SHORT_PENDING, MOCK_ROBOTS
from app.services.map_data import (
    get_region_by_slug,
    has_region_catalogue,
    list_regions,
    resolve_related_bosses,
    resolve_related_items,
)
from app.services.seo import meta_description
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["maps"])

_MAP_PAGE_TITLE = page_title("지도")
_MAP_PAGE_DESCRIPTION = PAGE_DESCRIPTIONS["maps"]
_MAP_WAITING_DESCRIPTION = PAGE_DESCRIPTIONS["maps"]

_UPCOMING_TOPICS = ("지역", "월드맵", "사냥터", "던전", "NPC", "성소")

_RELATED_LINKS = (
    {"label": "클래스", "route_name": "classes"},
    {"label": "보스", "route_name": "bosses"},
    {"label": "아이템", "route_name": "items"},
    {"label": "홈", "route_name": "home"},
)


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "maps",
    }


@router.get("/maps", response_class=HTMLResponse, name="maps")
def maps_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    regions = list_regions()
    catalogue_ready = has_region_catalogue()

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "지도", "route_name": "maps", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("지도", settings.absolute_url("/maps")),
            ],
        ),
    ]
    description = (
        _MAP_PAGE_DESCRIPTION if catalogue_ready else _MAP_WAITING_DESCRIPTION
    )
    context = {
        **_layout(request),
        "regions": regions,
        "region_count": len(regions),
        "catalogue_ready": catalogue_ready,
        "pending_label": MAP_PENDING_LABEL,
        "short_pending": MAP_SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "related_links": _RELATED_LINKS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_MAP_PAGE_TITLE,
            description=description,
            canonical_url=settings.absolute_url("/maps"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "maps/index.html", context)


@router.get("/maps/{slug}", response_class=HTMLResponse, name="map_detail")
def map_detail(request: Request, slug: str) -> HTMLResponse:
    region = get_region_by_slug(slug)
    if region is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    page_path = f"/maps/{slug}"
    page_url = settings.absolute_url(page_path)
    others = [r for r in list_regions() if r.slug != slug]

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "지도", "route_name": "maps", "current": False},
        {"label": region.name, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("지도", settings.absolute_url("/maps")),
                (region.name, page_url),
            ],
        ),
    ]

    info_cards: list[dict[str, str]] = []
    if region.region_kind and not region.region_kind_pending:
        info_cards.append({"title": "유형", "body": region.region_kind})
    if region.world_label and not region.world_label_pending:
        info_cards.append({"title": "월드", "body": region.world_label})

    summary_display = (
        MAP_PENDING_LABEL
        if region.summary_pending or not region.summary
        else region.summary
    )

    show_map_image = bool(region.map_image_url) and not region.map_image_pending
    npc_display = (
        region.npc_labels
        if region.npc_labels and not region.npc_pending
        else ()
    )

    context = {
        **_layout(request),
        "region": region,
        "related_regions": others,
        "related_bosses": resolve_related_bosses(region.related_boss_slugs),
        "related_items": resolve_related_items(region.related_item_slugs),
        "info_cards": info_cards,
        "summary_display": summary_display,
        "show_map_image": show_map_image,
        "npc_display": npc_display,
        "pending_label": MAP_PENDING_LABEL,
        "short_pending": MAP_SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=detail_title(region.name),
            description=meta_description(region.summary, fallback=_MAP_PAGE_DESCRIPTION),
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "maps/detail.html", context)
