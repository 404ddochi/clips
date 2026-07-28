"""Patch notes Patch Timeline list / search / filter tests."""

from __future__ import annotations

from app.main import app
from app.services import patch_mock_data
from app.services.patch_mock_data import PATCH_NOTES
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

_OLD_SAMPLE_TITLES = (
    "패치노트 요약 구조 샘플",
    "가독성 점검용 패치 샘플",
)
_TYPE_FILTER_LABELS = (
    "전체",
    "업데이트",
    "밸런스",
    "버그 수정",
    "시스템",
    "이벤트",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _assert_not_legacy_news_list(html: str, soup: BeautifulSoup) -> None:
    assert "검색 기능 준비 중" not in html
    assert "최신순 (준비 중)" not in html
    assert soup.select_one('input[disabled][type="search"]') is None
    assert soup.select_one(".filter-bar") is None
    assert soup.select_one(".news-list") is None
    for title in _OLD_SAMPLE_TITLES:
        assert title not in html


def test_patch_notes_route_endpoint() -> None:
    assert app.url_path_for("news_patch_notes") == "/news/patch-notes"
    from app.routers import news as news_router

    route = next(
        r
        for r in news_router.router.routes
        if getattr(r, "name", None) == "news_patch_notes"
    )
    assert route.path == "/news/patch-notes"
    assert route.endpoint.__name__ == "news_patch_notes"
    assert route.endpoint.__module__ == "app.routers.news"


def test_patch_notes_page_ok(client: TestClient) -> None:
    response = client.get("/news/patch-notes")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    _assert_not_legacy_news_list(html, soup)
    assert len(soup.find_all("h1")) == 1
    assert "패치노트" in soup.find("h1").get_text()
    assert 'href="' in html and "patch_notes.css" in html
    assert soup.find("ol", class_="patch-timeline") is not None
    assert soup.select(".patch-timeline__item")
    assert soup.find("nav", attrs={"aria-label": "패치 유형 필터"}) is not None
    assert soup.find("form", class_="patch-search") is not None
    search = soup.find("input", id="patch-search-q")
    assert search is not None
    assert not search.has_attr("disabled")
    assert search.get("placeholder") == "버전, 제목, 변경점, 키워드"


def test_patch_notes_seo(client: TestClient) -> None:
    soup = _soup(client.get("/news/patch-notes").text)
    title = soup.find("title")
    assert title is not None
    assert title.get_text() == (
        "패치노트 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트"
    )
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc is not None
    assert "패치노트" in desc.get("content", "")
    assert "버전별" in desc.get("content", "")
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    assert "noindex" in robots.get("content", "")


def test_patch_notes_renders_mock_list(client: TestClient) -> None:
    response = client.get("/news/patch-notes")
    html = response.text
    soup = _soup(html)
    _assert_not_legacy_news_list(html, soup)
    assert len(soup.select(".patch-timeline__item")) == len(PATCH_NOTES)
    assert len(soup.select(".patch-row")) == len(PATCH_NOTES)
    version_nodes = soup.select(".patch-row__version")
    versions_text = " ".join(el.get_text(" ", strip=True) for el in version_nodes)
    assert "v1.0.7" in versions_text
    assert "v1.0.1" in versions_text
    assert soup.find("time", attrs={"datetime": True}) is not None
    badges = {el.get_text(strip=True) for el in soup.select(".patch-badge")}
    assert {"업데이트", "밸런스", "버그 수정", "시스템", "이벤트"}.issubset(badges)
    detail = soup.find("a", class_="patch-row__detail")
    assert detail is not None
    assert "변경점 보기" in detail.get_text()
    assert "/news/patch-notes/" in detail.get("href", "")
    summary = soup.find("p", class_="patch-summary")
    assert summary is not None
    assert f"{len(PATCH_NOTES)}개" in summary.get_text()


def test_patch_notes_type_filters_present(client: TestClient) -> None:
    soup = _soup(client.get("/news/patch-notes").text)
    nav = soup.find("nav", attrs={"aria-label": "패치 유형 필터"})
    assert nav is not None
    labels = [a.get_text(strip=True) for a in nav.select(".patch-filters__link")]
    assert labels == list(_TYPE_FILTER_LABELS)
    assert len(labels) == 6


def test_patch_notes_search(client: TestClient) -> None:
    full = len(_soup(client.get("/news/patch-notes").text).select(".patch-row"))
    response = client.get("/news/patch-notes", params={"q": "밸런스"})
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    _assert_not_legacy_news_list(html, soup)
    assert "밸런스" in soup.find("input", id="patch-search-q").get("value", "")
    count = soup.find("span", class_="patch-summary__count")
    assert count is not None
    assert "개" in count.get_text()
    rows = soup.select(".patch-row")
    assert len(rows) >= 1
    assert len(rows) < full
    for row in rows:
        assert "밸런스" in row.get_text()
    assert soup.find("a", class_="patch-search__clear") is not None


def test_patch_notes_filter_type(client: TestClient) -> None:
    full = len(_soup(client.get("/news/patch-notes").text).select(".patch-row"))
    response = client.get("/news/patch-notes", params={"type": "balance"})
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    _assert_not_legacy_news_list(html, soup)
    active = soup.select_one(".patch-filters__link.is-active")
    assert active is not None
    assert active.get_text(strip=True) == "밸런스"
    assert active.get("aria-current") == "page"
    rows = soup.select(".patch-row")
    assert len(rows) >= 1
    assert len(rows) < full
    for row in rows:
        badges = {b.get_text(strip=True) for b in row.select(".patch-badge")}
        assert "밸런스" in badges


def test_patch_notes_search_and_filter(client: TestClient) -> None:
    response = client.get(
        "/news/patch-notes",
        params={"type": "balance", "q": "클래스"},
    )
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    _assert_not_legacy_news_list(html, soup)
    assert soup.find("input", id="patch-search-q").get("value") == "클래스"
    active = soup.select_one(".patch-filters__link.is-active")
    assert active is not None
    assert active.get_text(strip=True) == "밸런스"
    assert len(soup.select(".patch-row")) >= 1
    assert "v1.0.6" in html


def test_patch_notes_empty_state(client: TestClient) -> None:
    response = client.get("/news/patch-notes", params={"q": "zzzz-no-match-xxxx"})
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)
    assert "검색 기능 준비 중" not in html
    assert "조건에 맞는 패치노트가 없습니다" in html
    assert soup.find("ol", class_="patch-timeline") is None
    clear = soup.find("a", string=lambda t: t and "전체 보기" in t)
    assert clear is not None
    assert clear.get("href", "").endswith("/news/patch-notes")
    count = soup.find("span", class_="patch-summary__count")
    assert count is not None
    assert count.get_text(strip=True) == "0개"


def test_patch_notes_detail_still_works(client: TestClient) -> None:
    slug = PATCH_NOTES[0].slug
    response = client.get(f"/news/patch-notes/{slug}")
    assert response.status_code == 200
    soup = _soup(response.text)
    assert len(soup.find_all("h1")) == 1


def test_patch_notes_css(client: TestClient) -> None:
    assert client.get("/static/css/pages/patch_notes.css").status_code == 200


def test_patch_notes_filter_helpers() -> None:
    assert len(patch_mock_data.filter_patch_notes(type_key="event")) >= 1
    assert len(patch_mock_data.filter_patch_notes(query="긴요약")) >= 1
    assert patch_mock_data.parse_patch_filter("nope") == "all"
    assert patch_mock_data.parse_patch_filter("system") == "system"
