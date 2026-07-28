"""Information pages (news / coupons) mock UI tests."""

from __future__ import annotations

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _assert_single_h1(soup: BeautifulSoup) -> None:
    assert len(soup.find_all("h1")) == 1


def _assert_index_follow(soup: BeautifulSoup) -> None:
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert robots.get("content", "") == "index, follow"


def _assert_no_hash_href(soup: BeautifulSoup) -> None:
    for anchor in soup.find_all("a", href=True):
        assert anchor["href"] != "#"


NEWS_LIST_PATHS = (
    "/news",
    "/news/notices",
    "/news/events",
    "/news/patch-notes",
)


def test_news_list_pages_ok(client: TestClient) -> None:
    for path in NEWS_LIST_PATHS:
        response = client.get(path)
        assert response.status_code == 200, path
        soup = _soup(response.text)
        _assert_single_h1(soup)
        _assert_index_follow(soup)
        _assert_no_hash_href(soup)
        nav = soup.find("nav", attrs={"aria-label": "소식 카테고리"})
        assert nav is not None
        labels = {a.get_text(strip=True) for a in nav.find_all("a")}
        assert {"전체", "공지", "이벤트", "패치노트"}.issubset(labels)


def test_news_titles(client: TestClient) -> None:
    cases = {
        "/news": "소식 - CLIPS",
        "/news/notices": "공지 - CLIPS",
        "/news/events": "이벤트 - CLIPS",
        "/news/patch-notes": "패치노트 - CLIPS",
        "/coupons": "쿠폰 - CLIPS",
    }
    for path, expected in cases.items():
        soup = _soup(client.get(path).text)
        title = soup.find("title")
        assert title is not None
        assert title.get_text() == expected


def test_news_detail_ok(client: TestClient) -> None:
    response = client.get("/news/notices/clips-news-structure-sample")
    assert response.status_code == 200
    soup = _soup(response.text)
    _assert_single_h1(soup)
    assert "소식 데이터 구조 검증용 샘플 공지" in soup.find("h1").get_text()
    _assert_index_follow(soup)
    breadcrumb = soup.find("nav", attrs={"aria-label": "breadcrumb"})
    assert breadcrumb is not None
    assert soup.find("time", attrs={"datetime": True}) is not None
    assert "비공식 정보 플랫폼" in response.text
    assert 'href="#"' not in response.text
    assert "원문 URL이 없는 Mock" in response.text


def test_news_detail_404(client: TestClient) -> None:
    response = client.get(
        "/news/notices/does-not-exist",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404


def test_news_detail_wrong_category_404(client: TestClient) -> None:
    response = client.get(
        "/news/events/clips-news-structure-sample",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404


def test_coupons_index(client: TestClient) -> None:
    response = client.get("/coupons")
    assert response.status_code == 200
    soup = _soup(response.text)
    _assert_single_h1(soup)
    _assert_index_follow(soup)
    assert "SAMPLE-COUPON" in response.text
    assert "CLIPS-DEMO" in response.text
    assert response.text.count("data-coupon-row") >= 5
    assert soup.select_one(".empty-state") is None
    assert soup.find("nav", attrs={"aria-label": "쿠폰 상태 필터"}) is not None
    assert soup.select_one(".coupon-summary__count") is not None
    assert "개" in soup.select_one(".coupon-summary__count").get_text()
    for label in ("전체", "사용 가능", "만료 임박", "종료"):
        assert label in response.text


def test_coupon_detail(client: TestClient) -> None:
    response = client.get("/coupons/sample-available-demo")
    assert response.status_code == 200
    soup = _soup(response.text)
    _assert_single_h1(soup)
    assert soup.find("time", attrs={"datetime": True}) is not None
    assert "SAMPLE-COUPON" in response.text
    assert "비공식" in response.text
    copy_buttons = [
        button for button in soup.find_all("button") if "복사" in button.get_text(" ", strip=True)
    ]
    assert copy_buttons
    assert any(not button.has_attr("disabled") for button in copy_buttons)


def test_coupon_detail_404(client: TestClient) -> None:
    response = client.get("/coupons/missing", headers={"Accept": "text/html"})
    assert response.status_code == 404


def test_info_page_css(client: TestClient) -> None:
    for path in (
        "/static/css/pages/news.css",
        "/static/css/pages/article.css",
        "/static/css/pages/coupons.css",
        "/static/css/pages/patch_notes.css",
    ):
        assert client.get(path).status_code == 200


def test_home_links_to_info_pages(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    hrefs = {a.get("href") for a in soup.find_all("a", href=True)}
    assert any(h.endswith("/news") or h.rstrip("/").endswith("/news") for h in hrefs)
    assert any("/coupons" in (h or "") for h in hrefs)
    assert any("/news/notices/" in (h or "") for h in hrefs)
    assert any("/news/events/" in (h or "") for h in hrefs)
    assert any("/news/patch-notes/" in (h or "") for h in hrefs)


def test_coming_soon_sections_remain(client: TestClient) -> None:
    for path in ("/contents",):
        response = client.get(path)
        assert response.status_code == 200
        assert "준비 중" in response.text


def test_guides_is_editorial_desk(client: TestClient) -> None:
    response = client.get("/guides")
    assert response.status_code == 200
    assert "CLIPS 공략을 준비하고 있습니다." in response.text
    assert "준비 중" not in _soup(response.text).find("h1").get_text()


def test_maps_is_waiting_catalogue(client: TestClient) -> None:
    response = client.get("/maps")
    assert response.status_code == 200
    assert "공식 지역 정보를 정리합니다." in response.text
    assert "공개 지역 정보 대기 중" in response.text
    assert "준비 중" not in _soup(response.text).find("h1").get_text()


def test_items_is_waiting_catalogue(client: TestClient) -> None:
    response = client.get("/items")
    assert response.status_code == 200
    assert "공식 아이템 정보를 정리합니다." in response.text
    assert "공식 아이템 정보 대기 중" in response.text
    assert "준비 중" not in _soup(response.text).find("h1").get_text()


def test_bosses_is_waiting_catalogue(client: TestClient) -> None:
    response = client.get("/bosses")
    assert response.status_code == 200
    assert "이클립스의 공식 보스 정보를 정리합니다." in response.text
    assert "공식 보스 정보 대기 중" in response.text
    assert "준비 중" not in _soup(response.text).find("h1").get_text()


def test_sitemap_includes_public_info_pages(client: TestClient) -> None:
    body = client.get("/sitemap.xml").text
    assert "<loc>http://testserver/</loc>" in body
    assert "<loc>http://testserver/news</loc>" in body
    assert "<loc>http://testserver/coupons</loc>" in body
    assert "/admin" not in body
    assert "/dev/" not in body
    assert "?" not in body


def test_filter_controls_disabled(client: TestClient) -> None:
    soup = _soup(client.get("/news/notices").text)
    search = soup.find("input", attrs={"type": "search"})
    assert search is not None
    assert search.has_attr("disabled")
    sort = soup.find("select")
    assert sort is not None
    assert sort.has_attr("disabled")
