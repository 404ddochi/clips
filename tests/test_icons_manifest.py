"""Favicon, Apple/Android icons, and Web App Manifest tests."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

ICONS = Path(__file__).resolve().parents[1] / "app/static/icons"
MANIFEST = Path(__file__).resolve().parents[1] / "app/static/site.webmanifest"

EXPECTED_PNG = {
    "favicon-16x16.png": (16, 16),
    "favicon-32x32.png": (32, 32),
    "apple-touch-icon.png": (180, 180),
    "android-chrome-192x192.png": (192, 192),
    "android-chrome-512x512.png": (512, 512),
    "maskable-icon-512x512.png": (512, 512),
}

STATIC_PATHS = (
    "/static/icons/favicon.svg",
    "/static/icons/favicon.ico",
    "/static/icons/favicon-16x16.png",
    "/static/icons/favicon-32x32.png",
    "/static/icons/apple-touch-icon.png",
    "/static/icons/android-chrome-192x192.png",
    "/static/icons/android-chrome-512x512.png",
    "/static/icons/maskable-icon-512x512.png",
    "/static/site.webmanifest",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def test_icon_files_exist_with_correct_png_sizes() -> None:
    assert (ICONS / "favicon.svg").is_file()
    ico = (ICONS / "favicon.ico").read_bytes()
    assert ico[:4] == b"\x00\x00\x01\x00"  # ICO header
    assert MANIFEST.is_file()
    for name, size in EXPECTED_PNG.items():
        path = ICONS / name
        assert path.is_file(), name
        assert _png_size(path) == size, name


def test_static_icon_and_manifest_responses(client: TestClient) -> None:
    expectations = {
        "/static/icons/favicon.svg": "image/svg+xml",
        "/static/icons/favicon.ico": "image/",
        "/static/icons/favicon-16x16.png": "image/png",
        "/static/icons/favicon-32x32.png": "image/png",
        "/static/icons/apple-touch-icon.png": "image/png",
        "/static/icons/android-chrome-192x192.png": "image/png",
        "/static/icons/android-chrome-512x512.png": "image/png",
        "/static/icons/maskable-icon-512x512.png": "image/png",
        "/static/site.webmanifest": "manifest",
    }
    for path in STATIC_PATHS:
        response = client.get(path)
        assert response.status_code == 200, path
        content_type = response.headers.get("content-type", "")
        needle = expectations[path]
        assert needle in content_type, f"{path} -> {content_type}"


def test_home_head_icon_links_once(client: TestClient) -> None:
    soup = _soup(client.get("/").text)

    svg = soup.find("link", rel="icon", attrs={"type": "image/svg+xml"})
    assert svg is not None
    assert str(svg.get("href", "")).endswith("/static/icons/favicon.svg")

    png32 = soup.find("link", rel="icon", attrs={"sizes": "32x32"})
    png16 = soup.find("link", rel="icon", attrs={"sizes": "16x16"})
    assert png32 is not None and str(png32.get("href", "")).endswith(
        "/static/icons/favicon-32x32.png"
    )
    assert png16 is not None and str(png16.get("href", "")).endswith(
        "/static/icons/favicon-16x16.png"
    )

    shortcut = soup.find("link", rel="shortcut icon")
    assert shortcut is not None
    assert str(shortcut.get("href", "")).endswith("/static/icons/favicon.ico")

    apple = soup.find("link", rel="apple-touch-icon")
    assert apple is not None
    assert str(apple.get("href", "")).endswith("/static/icons/apple-touch-icon.png")

    manifest = soup.find("link", rel="manifest")
    assert manifest is not None
    assert str(manifest.get("href", "")).endswith("/static/site.webmanifest")

    assert len(soup.find_all("link", rel="manifest")) == 1
    assert len(soup.find_all("link", rel="apple-touch-icon")) == 1
    assert len(soup.find_all("link", rel="shortcut icon")) == 1
    assert len(soup.find_all("meta", attrs={"name": "theme-color"})) >= 1

    # OG tags still present and not duplicated
    assert len(soup.find_all("meta", attrs={"property": "og:image"})) == 1
    assert len(soup.find_all("meta", attrs={"property": "og:title"})) == 1


def test_site_webmanifest_json(client: TestClient) -> None:
    response = client.get("/static/site.webmanifest")
    assert response.status_code == 200
    payload = json.loads(response.text)
    assert payload["name"].startswith("CLIPS")
    assert payload["short_name"] == "CLIPS"
    assert payload["start_url"] == "/"
    assert payload["scope"] == "/"
    assert payload["display"] == "standalone"
    assert payload["lang"] == "ko-KR"
    assert payload["theme_color"] == "#080b12"
    assert payload["background_color"] == "#080b12"
    icons = payload["icons"]
    assert len(icons) == 3
    by_purpose = {(item["sizes"], item.get("purpose", "any")): item for item in icons}
    assert by_purpose[("192x192", "any")]["src"] == (
        "/static/icons/android-chrome-192x192.png"
    )
    assert by_purpose[("512x512", "any")]["src"] == (
        "/static/icons/android-chrome-512x512.png"
    )
    assert by_purpose[("512x512", "maskable")]["src"] == (
        "/static/icons/maskable-icon-512x512.png"
    )
