"""SEO-related routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from app.config import get_settings
from app.services.seo import build_robots_txt, build_sitemap_xml

router = APIRouter(tags=["seo"])


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt() -> str:
    return build_robots_txt(get_settings())


@router.get("/sitemap.xml")
def sitemap_xml() -> Response:
    body = build_sitemap_xml(get_settings())
    return Response(content=body, media_type="application/xml")
