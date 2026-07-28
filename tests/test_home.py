"""Home, UI, and static asset tests."""

from __future__ import annotations

import json

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_home_returns_200(client: TestClient) -> None:
    assert client.get("/").status_code == 200


def test_home_single_h1(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    assert len(soup.find_all("h1")) == 1


def test_home_clips_logo(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    logo = soup.select_one(".logo .logo-text")
    assert logo is not None
    assert "CLIPS" in logo.get_text()


def test_home_primary_nav_links(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    nav = soup.find("nav", attrs={"aria-label": "주요 메뉴"})
    assert nav is not None
    labels = {"홈", "소식", "클래스", "콘텐츠", "아이템", "보스", "지도", "공략", "쿠폰"}
    link_text = {a.get_text(strip=True) for a in nav.find_all("a")}
    assert labels.issubset(link_text)


def test_home_meta_description(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    tag = soup.find("meta", attrs={"name": "description"})
    assert tag is not None
    content = tag.get("content", "")
    assert "이클립스: 더 어웨이크닝" in content
    assert "비공식 정보 플랫폼" in content


def test_home_title(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    expected = "CLIPS - 이클립스: 더 어웨이크닝 정보 사이트"
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == expected
    og_title = soup.find("meta", attrs={"property": "og:title"})
    assert og_title is not None
    assert og_title.get("content") == expected


def test_home_json_ld_site_and_game_names(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    payloads = [json.loads(script.string or "") for script in scripts]
    website = next(item for item in payloads if item.get("@type") == "WebSite")
    assert website["name"] == "CLIPS"
    assert website["about"]["name"] == "이클립스: 더 어웨이크닝"
    assert website["about"]["alternateName"] == "Eclipse: The Awakening"
    webpage = next(item for item in payloads if item.get("@type") == "WebPage")
    assert webpage["isPartOf"]["name"] == "CLIPS"
    assert webpage["about"]["name"] == "이클립스: 더 어웨이크닝"


def test_home_hero_hierarchy(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    h1 = soup.find("h1")
    assert h1 is not None
    h1_text = " ".join(h1.get_text().split())
    assert h1_text == "이클립스: 더 어웨이크닝"
    lines = h1.select(".hero-title__line")
    assert len(lines) == 2
    assert lines[0].get_text(strip=True) == "이클립스: 더"
    assert lines[1].get_text(strip=True) == "어웨이크닝"
    assert soup.select_one(".hero-game-en") is not None
    assert "Eclipse: The Awakening" in soup.select_one(".hero-game-en").get_text()
    assert soup.select_one(".hero-brand") is not None
    assert soup.select_one(".eclipse") is not None
    logo_sub = soup.select_one(".logo-sub")
    assert logo_sub is not None
    assert "Eclipse: The Awakening" in logo_sub.get_text()


def test_home_info_strip(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    strip = soup.select_one(".info-strip")
    assert strip is not None
    labels = {el.get_text(strip=True) for el in strip.select(".info-strip__label")}
    assert {"최신 공지", "이벤트", "패치노트", "쿠폰"}.issubset(labels)


def test_home_section_order(client: TestClient) -> None:
    html = client.get("/").text
    hero = html.find('class="hero"')
    strip = html.find("info-strip")
    news = html.find("latest-news-heading")
    quick = html.find("quick-menu-heading")
    assert hero != -1 and strip != -1 and news != -1 and quick != -1
    assert hero < strip < news < quick


def test_home_outline_icons(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    icons = soup.select(".quick-menu-card .icon")
    assert len(icons) >= 8
    assert icons[0].get("fill") == "none"
    assert icons[0].attrs.get("viewbox") == "0 0 24 24"
    assert icons[0].get("width") == "20"
    stroked = icons[0].select_one("[stroke]")
    assert stroked is not None
    assert stroked.get("stroke-width") == "1.8"
    strip_icons = soup.select(".info-strip .icon")
    assert len(strip_icons) >= 4
    assert strip_icons[0].select_one("[stroke]").get("stroke-width") == "1.8"


def test_home_canonical(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    link = soup.find("link", rel="canonical")
    assert link is not None
    assert link.get("href") == "http://testserver/"


def test_home_json_ld(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    assert len(scripts) >= 1
    for script in scripts:
        json.loads(script.string or "")


def test_home_no_empty_hash_links(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    for anchor in soup.find_all("a", href=True):
        assert anchor["href"] != "#"


def test_home_unofficial_disclaimer(client: TestClient) -> None:
    html = client.get("/").text
    assert "비공식" in html
    assert "공식 홈페이지" not in html


def test_classes_page_live(client: TestClient) -> None:
    response = client.get("/classes")
    assert response.status_code == 200
    soup = _soup(response.text)
    assert len(soup.find_all("h1")) == 1
    assert "클래스" in soup.find("h1").get_text()
    assert "파이터" in response.text
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert "noindex" in robots.get("content", "")
    breadcrumb = soup.find("nav", attrs={"aria-label": "breadcrumb"})
    assert breadcrumb is not None
    assert breadcrumb.find("a", string="홈") is not None


def test_static_css_js(client: TestClient) -> None:
    for path in (
        "/static/css/tokens.css",
        "/static/css/components.css",
        "/static/css/utilities.css",
        "/static/js/common.js",
        "/static/js/theme.js",
    ):
        assert client.get(path).status_code == 200


def test_robots_txt(client: TestClient) -> None:
    response = client.get("/robots.txt")
    assert response.status_code == 200
    body = response.text
    assert "User-agent: *" in body
    assert "Sitemap: http://testserver/sitemap.xml" in body


def test_sitemap_xml(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    body = response.text
    assert "<loc>http://testserver/</loc>" in body
    assert "<lastmod>" in body


def test_not_found_page(client: TestClient) -> None:
    response = client.get("/does-not-exist", headers={"Accept": "text/html"})
    assert response.status_code == 404
    assert "페이지를 찾을 수 없습니다" in response.text
    assert "not_found.css" in response.text


def test_home_contains_clips_branding(client: TestClient) -> None:
    assert "CLIPS" in client.get("/").text
