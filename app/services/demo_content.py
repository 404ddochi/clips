"""Gate for development mock catalogues (news / coupons / patches)."""

from __future__ import annotations

from app.config import get_settings


def demo_content_enabled() -> bool:
    """Return True when in-memory mock catalogues may be served publicly."""
    return get_settings().allows_demo_content()
