"""SEO-related routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.config import get_settings
from app.services.seo import build_robots_txt, build_sitemap_xml

router = APIRouter(tags=["seo"])


@router.get("/robots.txt")
def robots_txt() -> Response:
    body = build_robots_txt(get_settings())
    return Response(
        content=body,
        media_type="text/plain; charset=utf-8",
    )


@router.get("/sitemap.xml")
def sitemap_xml() -> Response:
    body = build_sitemap_xml(get_settings())
    return Response(
        content=body,
        media_type="application/xml; charset=utf-8",
    )