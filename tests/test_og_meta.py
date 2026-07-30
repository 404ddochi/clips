"""Open Graph share image and meta tag tests."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

OG_PNG = Path(__file__).resolve().parents[1] / "app/static/images/og/clips-og.png"
OG_SVG = Path(__file__).resolve().parents[1] / "app/static/images/og/clips-og.svg"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_og_assets_exist_on_disk() -> None:
    assert OG_SVG.is_file()
    assert OG_PNG.is_file()
    assert OG_SVG.read_text(encoding="utf-8").startswith("<?xml")
    assert "CLIPS" in OG_SVG.read_text(encoding="utf-8")
    assert OG_PNG.stat().st_size > 10_000


def test_og_static_png_response(client: TestClient) -> None:
    response = client.get("/static/images/og/clips-og.png")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_og_static_svg_response(client: TestClient) -> None:
    response = client.get("/static/images/og/clips-og.svg")
    assert response.status_code == 200
    assert "svg" in response.headers["content-type"]
    assert b"viewBox" in response.content


def test_home_og_meta_single_and_complete(client: TestClient) -> None:
    soup = _soup(client.get("/").text)
    assert len(soup.find_all("meta", attrs={"property": "og:title"})) == 1
    assert len(soup.find_all("meta", attrs={"property": "og:description"})) == 1
    assert len(soup.find_all("meta", attrs={"property": "og:image"})) == 1
    assert soup.find("meta", attrs={"property": "og:type"})["content"] == "website"
    assert soup.find("meta", attrs={"property": "og:locale"})["content"] == "ko_KR"
    assert soup.find("meta", attrs={"property": "og:site_name"})["content"] == "CLIPS"
    assert soup.find("meta", attrs={"property": "og:image"})["content"].endswith(
        "/static/images/og/clips-og.png"
    )
    assert soup.find("meta", attrs={"property": "og:image:width"})["content"] == "1200"
    assert soup.find("meta", attrs={"property": "og:image:height"})["content"] == "630"
    assert soup.find("meta", attrs={"name": "twitter:card"})["content"] == (
        "summary_large_image"
    )
    assert soup.find("meta", attrs={"name": "twitter:image:alt"}) is not None


def test_production_og_image_uses_https(
    production_client: TestClient,
) -> None:
    soup = _soup(production_client.get("/").text)
    og_image = soup.find("meta", attrs={"property": "og:image"})["content"]
    assert og_image.startswith("https://")
    assert og_image.endswith("/static/images/og/clips-og.png")
    secure = soup.find("meta", attrs={"property": "og:image:secure_url"})
    assert secure is not None
    assert secure["content"] == og_image
