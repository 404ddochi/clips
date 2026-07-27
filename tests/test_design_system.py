"""CLIPS Design Language (CDL) showcase and gating tests."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_design_system_local_ok(local_client: TestClient) -> None:
    response = local_client.get("/dev/design-system")
    assert response.status_code == 200
    soup = _soup(response.text)
    assert len(soup.find_all("h1")) == 1
    assert "디자인 시스템" in soup.find("h1").get_text()


def test_design_system_robots_noindex(local_client: TestClient) -> None:
    soup = _soup(local_client.get("/dev/design-system").text)
    robots = soup.find("meta", attrs={"name": "robots"})
    assert robots is not None
    content = robots.get("content", "")
    assert "noindex" in content
    assert "nofollow" in content


def test_design_system_not_in_sitemap(local_client: TestClient) -> None:
    body = local_client.get("/sitemap.xml").text
    assert "/dev/design-system" not in body


def test_design_system_production_404(production_client: TestClient) -> None:
    response = production_client.get(
        "/dev/design-system",
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 404


def test_design_system_no_empty_hash(local_client: TestClient) -> None:
    soup = _soup(local_client.get("/dev/design-system").text)
    for anchor in soup.find_all("a", href=True):
        assert anchor["href"] != "#"


def test_design_system_icon_specs(local_client: TestClient) -> None:
    soup = _soup(local_client.get("/dev/design-system").text)
    icons = soup.select(".ds-icon-card .icon")
    assert len(icons) >= 20
    for svg in icons:
        assert svg.attrs.get("viewbox") == "0 0 24 24"
        assert svg.get("fill") == "none"
        stroked = svg.select_one("[stroke-width]")
        assert stroked is not None
        assert stroked.get("stroke-width") == "1.8"


def test_design_system_no_emoji(local_client: TestClient) -> None:
    html = local_client.get("/dev/design-system").text
    # Common pictographic emoji ranges used in product UI misuse
    emoji_re = re.compile(
        "["
        "\U0001f300-\U0001f5ff"
        "\U0001f600-\U0001f64f"
        "\U0001f680-\U0001f6ff"
        "\U0001f900-\U0001f9ff"
        "\U0001fa70-\U0001faff"
        "\u2600-\u26ff"
        "\u2700-\u27bf"
        "]"
    )
    assert emoji_re.search(html) is None


def test_design_system_cdl_classes(local_client: TestClient) -> None:
    html = local_client.get("/dev/design-system").text
    for class_name in (
        "button--primary",
        "card--interactive",
        "badge--notice",
        "tag--interactive",
        "status--success",
        "form-input",
        "table-wrap",
        "tabs__button",
        "pagination__link",
        "modal__dialog",
        "toast--info",
        "article__body",
        "empty-state",
        "text-section-title",
    ):
        assert class_name in html


def test_design_system_css_available(local_client: TestClient) -> None:
    assert local_client.get("/static/css/pages/design-system.css").status_code == 200
    assert local_client.get("/static/css/utilities.css").status_code == 200
    assert local_client.get("/static/css/tokens.css").status_code == 200
