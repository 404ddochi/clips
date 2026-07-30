"""Shared FastAPI dependencies."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.config import Settings, get_settings
from app.core.constants import (
    DEFAULT_HOME_DESCRIPTION,
    DEFAULT_HOME_TITLE,
    DEFAULT_OG_IMAGE_ALT,
    DEFAULT_OG_IMAGE_HEIGHT,
    DEFAULT_OG_IMAGE_PATH,
    DEFAULT_OG_IMAGE_TYPE,
    DEFAULT_OG_IMAGE_WIDTH,
    DEFAULT_OG_LOCALE,
    FOOTER_DISCLAIMER,
    GAME_TITLE,
    GAME_TITLE_EN,
    PUBLIC_ROBOTS,
)
from app.services.structured_data import collect_json_ld_items

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"


def _json_script(value: object) -> Markup:
    import json

    # Escape "<" so embedded JSON cannot break out of </script>.
    payload = json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")
    return Markup(payload)


def current_year_kst() -> int:
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    return datetime.now(tz).year


@lru_cache
def get_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    settings = get_settings()
    templates.env.globals["settings"] = settings
    templates.env.globals["absolute_url"] = settings.absolute_url
    templates.env.globals["app_name"] = settings.app_name
    templates.env.globals["site_name"] = "CLIPS"
    templates.env.globals["default_locale"] = settings.default_locale
    templates.env.globals["current_year"] = current_year_kst()
    templates.env.globals["game_title"] = GAME_TITLE
    templates.env.globals["game_title_en"] = GAME_TITLE_EN
    templates.env.globals["footer_disclaimer"] = FOOTER_DISCLAIMER
    templates.env.globals["allows_demo_content"] = (
        lambda: get_settings().allows_demo_content()
    )
    templates.env.filters["tojson"] = _json_script
    return templates


def get_app_settings() -> Settings:
    return get_settings()


def seo_context(
    *,
    title: str | None = None,
    description: str | None = None,
    canonical_url: str | None = None,
    og_title: str | None = None,
    og_description: str | None = None,
    og_image: str | None = None,
    og_type: str = "website",
    og_url: str | None = None,
    twitter_card: str = "summary_large_image",
    twitter_title: str | None = None,
    twitter_description: str | None = None,
    twitter_image: str | None = None,
    robots: str = PUBLIC_ROBOTS,
    structured_data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build template context keys consumed by `components/seo_meta.html`."""
    settings = get_settings()
    resolved_title = (title or "").strip() or DEFAULT_HOME_TITLE
    resolved_description = (description or "").strip() or DEFAULT_HOME_DESCRIPTION
    resolved_og_title = (og_title or resolved_title).strip()
    resolved_og_description = (og_description or resolved_description).strip()
    resolved_twitter_title = (twitter_title or resolved_og_title).strip()
    resolved_twitter_description = (
        twitter_description or resolved_og_description
    ).strip()
    resolved_canonical = (canonical_url or "").strip()
    resolved_og_url = (og_url or resolved_canonical).strip()
    resolved_og_image = (og_image or "").strip()
    if not resolved_og_image:
        resolved_og_image = settings.absolute_url(DEFAULT_OG_IMAGE_PATH)
    elif resolved_og_image.startswith("/"):
        resolved_og_image = settings.absolute_url(resolved_og_image)
    resolved_twitter_image = (twitter_image or resolved_og_image).strip()
    if resolved_twitter_image.startswith("/"):
        resolved_twitter_image = settings.absolute_url(resolved_twitter_image)
    secure_image = (
        resolved_og_image if resolved_og_image.startswith("https://") else None
    )
    image_alt = DEFAULT_OG_IMAGE_ALT
    json_ld_items = collect_json_ld_items(*(structured_data or []))

    return {
        "seo_title": resolved_title,
        "seo_description": resolved_description,
        "seo_canonical_url": resolved_canonical or None,
        "seo_robots": robots,
        "seo_og_type": og_type or "website",
        "seo_og_locale": DEFAULT_OG_LOCALE,
        "seo_og_title": resolved_og_title,
        "seo_og_description": resolved_og_description,
        "seo_og_url": resolved_og_url or None,
        "seo_og_image": resolved_og_image,
        "seo_og_image_secure_url": secure_image,
        "seo_og_image_type": DEFAULT_OG_IMAGE_TYPE,
        "seo_og_image_width": DEFAULT_OG_IMAGE_WIDTH,
        "seo_og_image_height": DEFAULT_OG_IMAGE_HEIGHT,
        "seo_og_image_alt": image_alt,
        "seo_twitter_card": twitter_card or "summary_large_image",
        "seo_twitter_title": resolved_twitter_title,
        "seo_twitter_description": resolved_twitter_description,
        "seo_twitter_image": resolved_twitter_image,
        "seo_twitter_image_alt": image_alt,
        "seo_structured_data": json_ld_items,
        "json_ld_items": json_ld_items,
    }
