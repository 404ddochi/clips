"""SEO helpers for sitemap, robots, meta text, and JSON-LD."""

from __future__ import annotations

import json
import re
from datetime import date
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring

from app.config import Settings
from app.core.constants import DEFAULT_PRODUCTION_SITE_URL, SITEMAP_PUBLIC_PATHS
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
    """Build robots.txt. Staging is fully closed; production/local allow crawl."""
    if settings.is_staging():
        return "User-agent: *\nDisallow: /\n"

    # Prefer the configured site origin; never advertise loopback to crawlers.
    sitemap_origin = settings.site_url
    host = (urlsplit(sitemap_origin).hostname or "").casefold()
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or host.endswith(".local"):
        sitemap_origin = DEFAULT_PRODUCTION_SITE_URL
    sitemap_url = f"{sitemap_origin.rstrip('/')}/sitemap.xml"

    # Only Disallow paths that exist (or are reserved and gated) in this app.
    # /dev is served and noindexed; /health is a probe (not for crawlers).
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /dev\n"
        "Disallow: /health\n"
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
    """Backward-compatible alias for home WebSite schema."""
    from app.services.structured_data import build_website_schema

    return build_website_schema(settings)


def build_home_json_ld(settings: Settings) -> dict[str, object]:
    """Deprecated WebPage payload — prefer ``build_home_structured_data``."""
    from app.services.structured_data import build_organization_schema

    return build_organization_schema(settings)


def json_ld_script(data: dict[str, object]) -> str:
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
