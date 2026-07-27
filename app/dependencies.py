"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"


def _json_script(value: object) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


@lru_cache
def get_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    settings = get_settings()
    templates.env.globals["settings"] = settings
    templates.env.globals["absolute_url"] = settings.absolute_url
    templates.env.globals["app_name"] = settings.app_name
    templates.env.globals["site_name"] = "클립스"
    templates.env.globals["default_locale"] = settings.default_locale
    templates.env.filters["tojson"] = _json_script
    return templates


def get_app_settings() -> Settings:
    return get_settings()


def seo_context(
    *,
    title: str,
    description: str,
    canonical_url: str,
    og_title: str | None = None,
    og_description: str | None = None,
    og_image: str | None = None,
    robots: str = "index, follow",
    structured_data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build template context keys consumed by `components/seo_meta.html`."""
    settings = get_settings()
    og_image_url = og_image or settings.absolute_url("/static/images/placeholders/og-default.svg")
    return {
        "seo_title": title,
        "seo_description": description,
        "seo_canonical_url": canonical_url,
        "seo_og_title": og_title or title,
        "seo_og_description": og_description or description,
        "seo_og_image": og_image_url,
        "seo_robots": robots,
        "seo_structured_data": structured_data or [],
    }
