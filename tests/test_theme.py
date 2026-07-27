"""Theme system markup and token tests."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_theme_bootstrap_script_in_head(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    scripts = soup.head.find_all("script") if soup.head else []
    inline = [s.get_text() for s in scripts if not s.get("src")]
    assert any("clips-theme" in text and "data-theme" in text for text in inline)


def test_theme_control_in_header(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    control = soup.select_one("[data-theme-control]")
    assert control is not None
    toggle = control.select_one("[data-theme-toggle]")
    assert toggle is not None
    assert toggle.get("aria-expanded") == "false"
    assert toggle.get("aria-controls") == "theme-menu"
    labels = {el.get_text(strip=True) for el in control.select("[data-theme-option]")}
    assert {"시스템 설정", "라이트 모드", "다크 모드"} <= labels
    for option in control.select("[data-theme-option]"):
        assert option.get_text(strip=True)
        assert option.select_one(".theme-menu__text") is not None


def test_theme_icons_specs(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    for name in ("theme-system", "theme-light", "theme-dark"):
        svg = soup.select_one(f".icon--{name}")
        assert svg is not None
        assert svg.attrs.get("viewbox") == "0 0 24 24"
        stroked = svg.select_one("[stroke-width]")
        assert stroked is not None
        assert stroked.get("stroke-width") == "1.8"


def test_theme_no_emoji_in_header_control(client: TestClient) -> None:
    control = _soup(client.get("/").text).select_one("[data-theme-control]")
    assert control is not None
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
    assert emoji_re.search(str(control)) is None


def test_theme_tokens_in_css(client: TestClient) -> None:
    css = client.get("/static/css/tokens.css").text
    assert 'html[data-theme="dark"]' in css
    assert 'html[data-theme="light"]' in css
    assert "--color-bg-root: #05070d" in css
    assert "--color-bg-root: #f3efe6" in css
    assert "color-scheme: dark" in css
    assert "color-scheme: light" in css


def test_theme_js_static(client: TestClient) -> None:
    assert client.get("/static/js/theme.js").status_code == 200
    body = client.get("/static/js/theme.js").text
    assert "clips-theme" in body
    assert "CLIPSTheme" in body


def test_theme_control_on_design_system(local_client: TestClient) -> None:
    soup = _soup(local_client.get("/dev/design-system").text)
    assert soup.select_one("[data-theme-control]") is not None


def test_home_title_unchanged_with_theme(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    assert soup.find("title").get_text() == "CLIPS - 이클립스: 더 어웨이크닝 정보 사이트"
    for anchor in soup.find_all("a", href=True):
        assert anchor["href"] != "#"
