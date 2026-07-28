"""Boss list and detail pages (publicly disclosed info only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.dependencies import get_templates, seo_context
from app.services.boss_data import get_boss_by_slug, has_boss_catalogue, list_bosses
from app.services.content_types import BOSS_PENDING_LABEL, BOSS_SHORT_PENDING, MOCK_ROBOTS
from app.services.seo_content import build_breadcrumb_json_ld

router = APIRouter(tags=["bosses"])

_BOSS_PAGE_TITLE = "보스 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
_BOSS_PAGE_DESCRIPTION = (
    "이클립스: 더 어웨이크닝 공식 보스 정보가 공개되면 CLIPS에서 업데이트합니다."
)
_BOSS_WAITING_DESCRIPTION = (
    "공식 보스 정보가 공개되면 업데이트됩니다. CLIPS는 비공식 정보 플랫폼입니다."
)

_UPCOMING_TOPICS = ("등장 시간", "위치", "드랍 아이템", "전투 정보", "공략")

_RELATED_LINKS = (
    {"label": "클래스", "route_name": "classes"},
    {"label": "소식", "route_name": "news"},
    {"label": "쿠폰", "route_name": "coupons"},
    {"label": "홈", "route_name": "home"},
)


def _layout(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "nav_items": MAIN_NAV,
        "active_menu": "bosses",
    }


@router.get("/bosses", response_class=HTMLResponse, name="bosses")
def bosses_index(request: Request) -> HTMLResponse:
    settings = get_settings()
    bosses = list_bosses()
    catalogue_ready = has_boss_catalogue()

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "보스", "route_name": "bosses", "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("보스", settings.absolute_url("/bosses")),
            ],
        ),
    ]
    description = (
        _BOSS_PAGE_DESCRIPTION if catalogue_ready else _BOSS_WAITING_DESCRIPTION
    )
    context = {
        **_layout(request),
        "bosses": bosses,
        "boss_count": len(bosses),
        "catalogue_ready": catalogue_ready,
        "pending_label": BOSS_PENDING_LABEL,
        "short_pending": BOSS_SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "related_links": _RELATED_LINKS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=_BOSS_PAGE_TITLE,
            description=description,
            canonical_url=settings.absolute_url("/bosses"),
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "bosses/index.html", context)


@router.get("/bosses/{slug}", response_class=HTMLResponse, name="boss_detail")
def boss_detail(request: Request, slug: str) -> HTMLResponse:
    item = get_boss_by_slug(slug)
    if item is None:
        raise HTTPException(status_code=404)

    settings = get_settings()
    page_path = f"/bosses/{slug}"
    page_url = settings.absolute_url(page_path)
    others = [b for b in list_bosses() if b.slug != slug]

    crumbs = (
        {"label": "홈", "route_name": "home", "current": False},
        {"label": "보스", "route_name": "bosses", "current": False},
        {"label": item.name, "href": page_path, "current": True},
    )
    structured = [
        build_breadcrumb_json_ld(
            settings,
            [
                ("홈", settings.absolute_url("/")),
                ("보스", settings.absolute_url("/bosses")),
                (item.name, page_url),
            ],
        ),
    ]

    info_cards: list[dict[str, str]] = []
    if item.category and not item.category_pending:
        info_cards.append({"title": "분류", "body": item.category})
    if item.region and not item.region_pending:
        info_cards.append({"title": "등장 지역", "body": item.region})

    summary_display = (
        BOSS_PENDING_LABEL
        if item.summary_pending or not item.summary
        else item.summary
    )

    context = {
        **_layout(request),
        "item": item,
        "related_bosses": others,
        "info_cards": info_cards,
        "summary_display": summary_display,
        "pending_label": BOSS_PENDING_LABEL,
        "short_pending": BOSS_SHORT_PENDING,
        "upcoming_topics": _UPCOMING_TOPICS,
        "breadcrumbs": crumbs,
        **seo_context(
            title=f"{item.name} - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트",
            description=item.summary or _BOSS_WAITING_DESCRIPTION,
            canonical_url=page_url,
            robots=MOCK_ROBOTS,
            structured_data=structured,
        ),
    }
    return get_templates().TemplateResponse(request, "bosses/detail.html", context)
