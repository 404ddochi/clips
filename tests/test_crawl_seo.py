"""Crawl-oriented SEO checks for robots, sitemap, and home JSON-LD."""

from __future__ import annotations

import json
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from app.config import Settings
from app.core.constants import DEFAULT_HOME_DESCRIPTION, DEFAULT_HOME_TITLE, SITEMAP_PUBLIC_PATHS
from app.services.seo import build_robots_txt, build_sitemap_xml
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _json_ld(html: str) -> list[dict[str, object]]:
    return [
        json.loads(script.string or "")
        for script in _soup(html).find_all(
            "script",
            attrs={"type": "application/ld+json"},
        )
    ]


def _sitemap_locs(xml: str) -> list[str]:
    root = ET.fromstring(xml)
    return [el.text or "" for el in root.findall("sm:url/sm:loc", _NS)]


def test_robots_and_sitemap_production_shape(production_client: TestClient) -> None:
    robots = production_client.get("/robots.txt")
    assert robots.status_code == 200
    assert "text/plain" in robots.headers["content-type"]
    assert "charset=utf-8" in robots.headers["content-type"]
    body = robots.text
    assert "User-agent: *" in body
    assert "Allow: /" in body
    assert "Disallow: /dev" in body
    assert "Disallow: /health" in body
    assert "Sitemap: https://example.com/sitemap.xml" in body
    assert "localhost" not in body
    assert "127.0.0.1" not in body

    sitemap = production_client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "application/xml" in sitemap.headers["content-type"]
    locs = _sitemap_locs(sitemap.text)
    assert locs
    assert len(locs) == len(set(locs))
    assert "https://example.com/" in locs
    for path in SITEMAP_PUBLIC_PATHS:
        assert f"https://example.com{path}" in locs
    for loc in locs:
        assert loc.startswith("https://example.com")
        assert "?" not in loc
        assert "#" not in loc
        path = urlsplit(loc).path or "/"
        assert path not in {"/health", "/search", "/robots.txt", "/sitemap.xml"}
        assert not path.startswith("/admin")
        assert not path.startswith("/dev")
        assert not path.startswith("/api")
        # Each sitemap URL must resolve publicly (demo catalogues empty in production).
        page = production_client.get(path, headers={"Accept": "text/html"})
        assert page.status_code == 200, path


def test_home_json_ld_crawl_contract(production_client: TestClient) -> None:
    html = production_client.get("/").text
    payloads = _json_ld(html)
    types = [item.get("@type") for item in payloads]
    assert types.count("WebSite") == 1
    assert types.count("Organization") == 1
    website = next(item for item in payloads if item["@type"] == "WebSite")
    organization = next(item for item in payloads if item["@type"] == "Organization")
    assert website["name"] == "CLIPS"
    assert website["alternateName"] == DEFAULT_HOME_TITLE
    assert website["description"] == DEFAULT_HOME_DESCRIPTION
    assert website["url"].startswith("https://")
    assert "비공식" in str(organization["description"])
    assert "sameAs" not in organization
    assert organization["logo"].endswith("/static/icons/android-chrome-512x512.png")
    action = website["potentialAction"]
    assert action["@type"] == "SearchAction"
    assert "/search?q={search_term_string}" in action["target"]["urlTemplate"]


def test_unknown_url_is_hard_404(client: TestClient) -> None:
    response = client.get(
        "/this-page-does-not-exist-for-seo",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404


def test_playclips_robots_builder_defaults() -> None:
    body = build_robots_txt(Settings(SITE_URL="https://playclips.kr"))
    assert body == (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /dev\n"
        "Disallow: /health\n"
        "Sitemap: https://playclips.kr/sitemap.xml\n"
    )
    xml = build_sitemap_xml(Settings(SITE_URL="https://playclips.kr"))
    locs = _sitemap_locs(xml)
    assert all(loc.startswith("https://playclips.kr") for loc in locs)
    assert "https://playclips.kr/" in locs
