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
from app.core.constants import FOOTER_DISCLAIMER, GAME_TITLE, GAME_TITLE_EN

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"


def _json_script(value: object) -> Markup:
    import json

    return Markup(json.dumps(value, ensure_ascii=False))


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
    templates.env.globals["site_name"] = "클립스"
    templates.env.globals["default_locale"] = settings.default_locale
    templates.env.globals["current_year"] = current_year_kst()
    templates.env.globals["game_title"] = GAME_TITLE
    templates.env.globals["game_title_en"] = GAME_TITLE_EN
    templates.env.globals["footer_disclaimer"] = FOOTER_DISCLAIMER
    templates.env.filters["tojson"] = _json_script
    return templates


def get_app_settings() -> Settings:
    return get_settings()


def seo_context(
    *,
    title: str,
    description: str,
    canonical_url: str | None = None,
    og_title: str | None = None,
    og_description: str | None = None,
    og_image: str | None = None,
    robots: str = "index, follow",
    structured_data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build template context keys consumed by `components/seo_meta.html`."""
    return {
        "seo_title": title,
        "seo_description": description,
        "seo_canonical_url": canonical_url or "",
        "seo_og_title": og_title or title,
        "seo_og_description": og_description or description,
        "seo_og_image": og_image,
        "seo_robots": robots,
        "seo_structured_data": structured_data or [],
    }
