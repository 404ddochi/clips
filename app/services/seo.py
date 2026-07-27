"""SEO helpers for sitemap, robots, and JSON-LD."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from app.config import Settings
from app.core.constants import DEFAULT_HOME_DESCRIPTION, DEFAULT_HOME_TITLE, SITEMAP_PUBLIC_PATHS


def current_sitemap_lastmod() -> str:
    """ISO 8601 date for sitemap lastmod (UTC, date portion only)."""
    return datetime.now(UTC).date().isoformat()


def build_robots_txt(settings: Settings) -> str:
    sitemap_url = settings.absolute_url("/sitemap.xml")
    return f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"


def build_sitemap_xml(settings: Settings) -> str:
    urlset = Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
    )
    lastmod = current_sitemap_lastmod()
    for path in SITEMAP_PUBLIC_PATHS:
        url_el = SubElement(urlset, "url")
        loc = SubElement(url_el, "loc")
        loc.text = settings.absolute_url(path)
        lastmod_el = SubElement(url_el, "lastmod")
        lastmod_el.text = lastmod
    return tostring(urlset, encoding="unicode")


def build_website_json_ld(settings: Settings) -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "클립스",
        "alternateName": "CLIPS",
        "url": settings.app_base_url,
        "description": DEFAULT_HOME_DESCRIPTION,
        "inLanguage": settings.default_locale,
    }


def build_home_json_ld(settings: Settings) -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": DEFAULT_HOME_TITLE,
        "description": DEFAULT_HOME_DESCRIPTION,
        "url": settings.absolute_url("/"),
        "isPartOf": {"@type": "WebSite", "url": settings.app_base_url, "name": "CLIPS"},
    }


def json_ld_script(data: dict[str, object]) -> str:
    return json.dumps(data, ensure_ascii=False)
