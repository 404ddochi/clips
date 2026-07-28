"""SEO helpers for sitemap, robots, meta text, and JSON-LD."""

from __future__ import annotations

import json
import re
from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring

from app.config import Settings
from app.core.constants import (
    DEFAULT_HOME_DESCRIPTION,
    DEFAULT_HOME_TITLE,
    SERVICE_NAME,
    SITEMAP_PUBLIC_PATHS,
)
from app.services.boss_data import list_bosses
from app.services.class_data import list_classes
from app.services.coupon_mock_data import list_coupons
from app.services.guide_data import list_published_guides
from app.services.item_data import list_items
from app.services.map_data import list_regions
from app.services.news_mock_data import list_news
from app.services.patch_mock_data import list_patch_notes

_WHITESPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")


def meta_description(
    text: str | None,
    *,
    fallback: str,
    max_length: int = 160,
) -> str:
    """Clean and shorten description text for meta tags."""
    raw = (text or "").strip()
    if not raw:
        return fallback
    cleaned = _TAG_RE.sub(" ", raw)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return fallback
    if len(cleaned) <= max_length:
        return cleaned
    truncated = cleaned[: max_length - 1].rstrip(" ,.;:")
    return f"{truncated}…"


def build_robots_txt(settings: Settings) -> str:
    sitemap_url = settings.canonical_url("/sitemap.xml")
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /dev\n"
        "Disallow: /api\n"
        f"Sitemap: {sitemap_url}\n"
    )


def _sitemap_entries(settings: Settings) -> list[tuple[str, date | None]]:
    """Stable ordered (absolute_url, optional lastmod) for public URLs."""
    entries: list[tuple[str, date | None]] = []
    seen: set[str] = set()

    def add(path: str, lastmod: date | None = None) -> None:
        loc = settings.canonical_url(path)
        if loc in seen:
            return
        seen.add(loc)
        entries.append((loc, lastmod))

    for path in SITEMAP_PUBLIC_PATHS:
        add(path)

    for notice in list_news(category="notice"):
        add(
            f"/news/notices/{notice.slug}",
            (notice.updated_at or notice.published_at).date(),
        )
    for event in list_news(category="event"):
        add(
            f"/news/events/{event.slug}",
            (event.updated_at or event.published_at).date(),
        )
    for patch in list_patch_notes():
        add(f"/news/patch-notes/{patch.slug}", patch.published_at.date())

    for class_item in list_classes():
        add(f"/classes/{class_item.slug}")

    for item_entry in list_items():
        add(f"/items/{item_entry.slug}")
    for boss in list_bosses():
        add(f"/bosses/{boss.slug}")
    for region in list_regions():
        add(f"/maps/{region.slug}")
    for guide in list_published_guides():
        add(f"/guides/{guide.slug}", guide.updated_at.date())

    for coupon in list_coupons():
        add(f"/coupons/{coupon.slug}", coupon.valid_from.date())

    return entries


def build_sitemap_xml(settings: Settings) -> str:
    urlset = Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
    )
    for loc, lastmod in _sitemap_entries(settings):
        url_el = SubElement(urlset, "url")
        loc_el = SubElement(url_el, "loc")
        loc_el.text = loc
        if lastmod is not None:
            lastmod_el = SubElement(url_el, "lastmod")
            lastmod_el.text = lastmod.isoformat()
    return tostring(urlset, encoding="unicode")


def build_website_json_ld(settings: Settings) -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SERVICE_NAME,
        "alternateName": ["클립스", "CLIPS", "Eclipse: The Awakening Info"],
        "url": settings.site_url,
        "description": DEFAULT_HOME_DESCRIPTION,
        "inLanguage": settings.default_locale,
        "about": {
            "@type": "VideoGame",
            "name": "이클립스: 더 어웨이크닝",
            "alternateName": "Eclipse: The Awakening",
        },
    }


def build_home_json_ld(settings: Settings) -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": DEFAULT_HOME_TITLE,
        "description": DEFAULT_HOME_DESCRIPTION,
        "url": settings.canonical_url("/"),
        "isPartOf": {
            "@type": "WebSite",
            "url": settings.site_url,
            "name": "CLIPS",
        },
        "about": {
            "@type": "VideoGame",
            "name": "이클립스: 더 어웨이크닝",
            "alternateName": "Eclipse: The Awakening",
        },
    }


def json_ld_script(data: dict[str, object]) -> str:
    return json.dumps(data, ensure_ascii=False)
