"""Coupon list UX tests (Coupon Row + SSR filters)."""

from __future__ import annotations

import re

import pytest
from app.services.coupon_mock_data import COUPON_ITEMS, filter_coupons
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_mock_source_counts() -> None:
    assert len(COUPON_ITEMS) >= 5
    assert len(filter_coupons("all")) == len(COUPON_ITEMS)
    assert len(filter_coupons("available")) >= 3
    assert len(filter_coupons("expiring")) >= 1
    assert len(filter_coupons("expired")) >= 1


def test_coupons_index_renders_mock_rows(client: TestClient) -> None:
    response = client.get("/coupons")
    assert response.status_code == 200
    html = response.text
    soup = _soup(html)

    assert len(soup.find_all("h1")) == 1
    assert soup.find("h1").get_text(strip=True) == "쿠폰"
    assert "SAMPLE-COUPON" in html
    assert "CLIPS-DEMO" in html
    assert "코드 복사" in html
    assert html.count("data-coupon-row") >= 5
    assert soup.select_one(".empty-state") is None
    assert "조건에 맞는 쿠폰이 없습니다" not in html

    for label in ("전체", "사용 가능", "만료 임박", "종료"):
        assert label in html

    summary = soup.select_one(".coupon-summary__count")
    assert summary is not None
    assert re.fullmatch(r"\d+개", summary.get_text(strip=True))
    assert int(summary.get_text(strip=True).removesuffix("개")) >= 5

    current = soup.select_one('.coupon-filters__link[aria-current="page"]')
    assert current is not None
    assert current.get_text(strip=True) == "전체"


def test_coupons_context_keys_drive_filters(client: TestClient) -> None:
    soup = _soup(client.get("/coupons").text)
    labels = [a.get_text(strip=True) for a in soup.select(".coupon-filters__link")]
    assert labels == ["전체", "사용 가능", "만료 임박", "종료"]
    assert all(label for label in labels)


def test_coupons_copy_buttons(client: TestClient) -> None:
    soup = _soup(client.get("/coupons").text)
    active_copies = soup.select("button[data-copy-text]")
    assert active_copies
    for button in active_copies:
        assert "코드 복사" in button.get_text(" ", strip=True)
        assert not button.has_attr("disabled")

    expired_rows = soup.select('.coupon-row[data-coupon-status="expired"]')
    assert expired_rows
    for row in expired_rows:
        button = row.select_one("button")
        assert button is not None
        assert button.has_attr("disabled")


def test_coupons_filter_available(client: TestClient) -> None:
    response = client.get("/coupons?status=available")
    soup = _soup(response.text)
    assert response.text.count("data-coupon-row") >= 3
    current = soup.select_one('.coupon-filters__link[aria-current="page"]')
    assert current is not None
    assert current.get_text(strip=True) == "사용 가능"
    for row in soup.select("[data-coupon-row]"):
        assert row.get("data-coupon-status") == "available"


def test_coupons_filter_expiring_and_expired(client: TestClient) -> None:
    expiring = client.get("/coupons?status=expiring")
    assert "data-coupon-row" in expiring.text
    soup_e = _soup(expiring.text)
    statuses = [r.get("data-coupon-status") for r in soup_e.select("[data-coupon-row]")]
    assert statuses and all(status == "expiring" for status in statuses)

    expired = client.get("/coupons?status=expired")
    soup_x = _soup(expired.text)
    assert soup_x.select("[data-coupon-row]")
    expired_statuses = [r.get("data-coupon-status") for r in soup_x.select("[data-coupon-row]")]
    assert all(status == "expired" for status in expired_statuses)
    assert all(b.has_attr("disabled") for b in soup_x.select(".coupon-row button"))


def test_coupons_invalid_status_falls_back_to_all(client: TestClient) -> None:
    response = client.get("/coupons?status=not-a-real-status")
    assert response.status_code == 200
    soup = _soup(response.text)
    current = soup.select_one('.coupon-filters__link[aria-current="page"]')
    assert current is not None
    assert current.get_text(strip=True) == "전체"
    assert response.text.count("data-coupon-row") >= 5


def test_coupons_empty_state(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.routers import coupons as coupons_router

    monkeypatch.setattr(coupons_router, "filter_coupons", lambda _key: ())
    response = client.get("/coupons?status=available")
    assert response.status_code == 200
    soup = _soup(response.text)
    assert soup.select_one(".empty-state") is not None
    assert "조건에 맞는 쿠폰이 없습니다" in response.text
    assert soup.select_one(".coupon-summary__count").get_text(strip=True) == "0개"
    assert response.text.count("data-coupon-row") == 0


def test_coupon_detail_copy_enabled_for_active(client: TestClient) -> None:
    soup = _soup(client.get("/coupons/sample-available-demo").text)
    button = soup.select_one("button[data-copy-text]")
    assert button is not None
    assert button["data-copy-text"] == "SAMPLE-COUPON"
    assert not button.has_attr("disabled")


def test_coupon_detail_copy_disabled_when_expired(client: TestClient) -> None:
    soup = _soup(client.get("/coupons/preparing-expired-sample").text)
    buttons = [b for b in soup.find_all("button") if "복사" in b.get_text(" ", strip=True)]
    assert buttons
    assert all(b.has_attr("disabled") for b in buttons)
