"""Health check API."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.core.constants import SERVICE_NAME

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "environment": settings.app_env,
    }
