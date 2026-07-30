"""Release readiness smoke checks for public surfaces."""

from __future__ import annotations

import json
from urllib.parse import urlsplit
from xml.etree import ElementTree

import pytest
from app.config import Settings, validate_settings
from app.services.coupon_mock_data import get_coupon_by_slug, list_coupons
from app.services.news_mock_data import get_news_by_slug, list_news
from app.services.patch_mock_data import get_patch_by_slug, list_patch_notes
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

PUBLIC_HUB_PATHS = (
    "/",
    "/search",
    "/news",
    "/news/notices",
    "/news/events",
    "/news/patch-notes",
    "/classes",
    "/contents",
    "/items",
    "/bosses",
    "/maps",
    "/guides",
    "/coupons",
    "/robots.txt",
    "/sitemap.xml",
    "/health",
)

_DEMO_MARKERS = (
    "SAMPLE-COUPON",
    "CLIPS-DEMO",
    "CLIPS-EXPIRE-SOON",
    "CLIPS Mock",
    "Mock 업데이트",
)

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


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


@pytest.mark.parametrize("path", PUBLIC_HUB_PATHS)
def test_public_hubs_ok(client: TestClient, path: str) -> None:
    response = client.get(path, headers={"Accept": "text/html"})
    assert response.status_code == 200


def test_unknown_path_is_404(client: TestClient) -> None:
    response = client.get(
        "/this-path-does-not-exist-clips",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404
    soup = _soup(response.text)
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert "noindex" in (robots.get("content") or "")


def test_sitemap_urls_are_absolute_and_reachable(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.headers.get("content-type", "")
    root = ElementTree.fromstring(response.text)
    locs = [el.text or "" for el in root.findall("sm:url/sm:loc", _SITEMAP_NS)]
    assert locs
    assert len(locs) == len(set(locs))
    joined = "\n".join(locs)
    assert "/search" not in joined
    assert "/admin" not in joined
    assert "/dev/" not in joined
    for loc in locs:
        parts = urlsplit(loc)
        assert parts.scheme in {"http", "https"}
        assert parts.netloc
        path = parts.path or "/"
        page = client.get(path, headers={"Accept": "text/html"})
        assert page.status_code == 200, path


def test_search_noindex_and_json_ld_parse(client: TestClient) -> None:
    html = client.get("/search?q=클래스").text
    soup = _soup(html)
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert "noindex" in (robots.get("content") or "")
    payloads = _json_ld(html)
    assert all(item.get("@type") != "Article" for item in payloads)


def test_home_search_action_and_canonical(client: TestClient) -> None:
    html = client.get("/").text
    soup = _soup(html)
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None
    href = canonical.get("href") or ""
    assert href.endswith("/") or href.endswith("testserver")
    assert "127.0.0.1" not in href
    website = next(item for item in _json_ld(html) if item.get("@type") == "WebSite")
    action = website["potentialAction"]
    assert action["@type"] == "SearchAction"
    assert action["target"]["urlTemplate"].endswith("/search?q={search_term_string}")


def test_static_assets_ok(client: TestClient) -> None:
    for path in (
        "/static/css/base.css",
        "/static/css/pages/home.css",
        "/static/js/theme.js",
        "/static/icons/favicon.svg",
    ):
        response = client.get(path)
        assert response.status_code == 200, path


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "Referrer-Policy" in response.headers


def test_production_hides_demo_catalogues(production_client: TestClient) -> None:
    assert list_news() == ()
    assert list_patch_notes() == ()
    assert list_coupons() == ()
    assert get_news_by_slug("notice", "clips-news-structure-sample") is None
    assert get_patch_by_slug("mock-patch-1-0-7") is None
    assert get_coupon_by_slug("sample-available-demo") is None

    home = production_client.get("/").text
    coupons = production_client.get("/coupons").text
    news = production_client.get("/news").text
    sitemap = production_client.get("/sitemap.xml").text
    for body in (home, coupons, news, sitemap):
        for marker in _DEMO_MARKERS:
            assert marker not in body, marker

    assert production_client.get("/coupons/sample-available-demo").status_code == 404
    assert production_client.get("/docs").status_code == 404
    assert production_client.get("/openapi.json").status_code == 404


def test_production_site_url_fail_fast() -> None:
    with pytest.raises(RuntimeError, match="https"):
        validate_settings(
            Settings(
                APP_ENV="production",
                APP_DEBUG=False,
                SECRET_KEY="production-test-secret-key-32chars",
                SITE_URL="http://example.com",
            )
        )
    with pytest.raises(RuntimeError, match="localhost"):
        validate_settings(
            Settings(
                APP_ENV="production",
                APP_DEBUG=False,
                SECRET_KEY="production-test-secret-key-32chars",
                SITE_URL="https://127.0.0.1",
            )
        )
    validate_settings(
        Settings(
            APP_ENV="production",
            APP_DEBUG=False,
            SECRET_KEY="production-test-secret-key-32chars",
            SITE_URL="https://clips.example.com",
        )
    )


def test_robots_staging_disallow_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SITE_URL", "https://staging.example.com")
    from app.config import get_settings
    from app.services.seo import build_robots_txt

    get_settings.cache_clear()
    try:
        body = build_robots_txt(get_settings())
        assert "Disallow: /" in body
        assert "Sitemap:" not in body
    finally:
        get_settings.cache_clear()


def test_home_internal_nav_links(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    hrefs: set[str] = set()
    for a in soup.select("header a[href], footer a[href], a.home-menu-card"):
        href = a.get("href")
        if not href:
            continue
        parts = urlsplit(str(href))
        path = parts.path or "/"
        if path.startswith("/"):
            hrefs.add(path)
    assert hrefs
    for path in hrefs:
        assert client.get(path, headers={"Accept": "text/html"}).status_code == 200
