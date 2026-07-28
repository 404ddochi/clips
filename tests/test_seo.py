"""SEO foundation tests: sitemap, robots, meta, SITE_URL."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from app.config import Settings, get_settings, normalize_canonical_path, normalize_site_url
from app.core.constants import DEFAULT_HOME_TITLE, PAGE_DESCRIPTIONS, SITEMAP_PUBLIC_PATHS
from app.services.class_data import list_classes
from app.services.coupon_mock_data import list_coupons
from app.services.news_mock_data import list_news
from app.services.patch_mock_data import list_patch_notes
from app.services.seo import build_robots_txt, build_sitemap_xml, meta_description
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _sitemap_locs(xml: str) -> list[str]:
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [el.text or "" for el in root.findall("sm:url/sm:loc", ns)]


def test_site_url_normalization() -> None:
    assert normalize_site_url("https://clips.example.com/") == "https://clips.example.com"
    assert normalize_canonical_path("/guides/?q=1#x") == "/guides"
    assert normalize_canonical_path("/") == "/"
    settings = Settings(SITE_URL="https://clips.example.com/")
    assert settings.site_url == "https://clips.example.com"
    assert settings.canonical_url("/guides?category=beginner") == (
        "https://clips.example.com/guides"
    )
    assert settings.canonical_url("guides/") == "https://clips.example.com/guides"


def test_meta_description_cleaning() -> None:
    assert meta_description(None, fallback="fallback") == "fallback"
    assert meta_description("  <b>안녕</b>   세상  ", fallback="x") == "안녕 세상"
    long = "가" * 200
    out = meta_description(long, fallback="x", max_length=20)
    assert out.endswith("…")
    assert len(out) <= 20


def test_robots_txt(client: TestClient) -> None:
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "User-agent: *" in body
    assert "Allow: /" in body
    assert "Disallow: /admin" in body
    assert "Disallow: /dev" in body
    assert "Disallow: /api" in body
    assert "Sitemap: http://testserver/sitemap.xml" in body
    assert "Disallow: /\n" not in body


def test_sitemap_xml_public_lists_and_details(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    locs = _sitemap_locs(response.text)
    assert len(locs) == len(set(locs))

    for path in SITEMAP_PUBLIC_PATHS:
        assert f"http://testserver{path}" in locs

    for item in list_news(category="notice"):
        assert f"http://testserver/news/notices/{item.slug}" in locs
    for item in list_classes():
        assert f"http://testserver/classes/{item.slug}" in locs
    for patch in list_patch_notes():
        assert f"http://testserver/news/patch-notes/{patch.slug}" in locs
    for coupon in list_coupons():
        assert f"http://testserver/coupons/{coupon.slug}" in locs

    joined = "\n".join(locs)
    assert "/admin" not in joined
    assert "/dev/" not in joined
    assert "?" not in joined


def test_sitemap_lastmod_only_on_details() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    xml = build_sitemap_xml(settings)
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = root.findall("sm:url", ns)
    by_loc = {
        (url.find("sm:loc", ns).text or ""): url.find("sm:lastmod", ns)
        for url in urls
        if url.find("sm:loc", ns) is not None
    }
    assert by_loc["http://testserver/"] is None
    notice = list_news(category="notice")[0]
    detail_lastmod = by_loc[f"http://testserver/news/notices/{notice.slug}"]
    assert detail_lastmod is not None
    assert detail_lastmod.text


def test_public_page_meta(client: TestClient) -> None:
    cases = {
        "/": (DEFAULT_HOME_TITLE, PAGE_DESCRIPTIONS["home"]),
        "/news": ("소식 - CLIPS", PAGE_DESCRIPTIONS["news"]),
        "/news/patch-notes": ("패치노트 - CLIPS", PAGE_DESCRIPTIONS["patch_notes"]),
        "/classes": ("클래스 - CLIPS", PAGE_DESCRIPTIONS["classes"]),
        "/contents": ("콘텐츠 - CLIPS", PAGE_DESCRIPTIONS["contents"]),
        "/items": ("아이템 - CLIPS", PAGE_DESCRIPTIONS["items"]),
        "/bosses": ("보스 - CLIPS", PAGE_DESCRIPTIONS["bosses"]),
        "/maps": ("지도 - CLIPS", PAGE_DESCRIPTIONS["maps"]),
        "/guides": ("공략 - CLIPS", PAGE_DESCRIPTIONS["guides"]),
        "/coupons": ("쿠폰 - CLIPS", PAGE_DESCRIPTIONS["coupons"]),
    }
    for path, (title, desc) in cases.items():
        soup = _soup(client.get(path).text)
        assert soup.find("title").get_text() == title, path
        meta_desc = soup.find("meta", attrs={"name": "description"})
        assert meta_desc is not None
        assert meta_desc.get("content") == desc, path
        robots = soup.find("meta", attrs={"name": "robots"})
        assert robots is not None
        assert robots.get("content") == "index, follow", path
        canonical = soup.find("link", rel="canonical")
        assert canonical is not None
        expected_canon = f"http://testserver{path}"
        assert canonical.get("href") == expected_canon, path
        assert soup.find("meta", attrs={"property": "og:title"}) is not None
        assert soup.find("meta", attrs={"property": "og:description"}) is not None
        og_url = soup.find("meta", attrs={"property": "og:url"})
        assert og_url is not None
        assert og_url.get("content") == expected_canon
        assert soup.find("meta", attrs={"name": "twitter:card"})["content"] == (
            "summary_large_image"
        )
        assert soup.find("meta", attrs={"property": "og:image"}) is None
        assert soup.find("meta", attrs={"name": "twitter:image"}) is None


def test_filtered_list_canonical_strips_query(client: TestClient) -> None:
    soup = _soup(client.get("/guides?q=test&category=beginner").text)
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None
    assert canonical.get("href") == "http://testserver/guides"


def test_dev_noindex(local_client: TestClient) -> None:
    soup = _soup(local_client.get("/dev/design-system").text)
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert "noindex" in robots.get("content", "")
    assert soup.find("link", rel="canonical") is None


def test_build_robots_txt_uses_site_url() -> None:
    settings = Settings(SITE_URL="https://clips.example.com")
    body = build_robots_txt(settings)
    assert "Sitemap: https://clips.example.com/sitemap.xml" in body
