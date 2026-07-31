"""Health check API."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.constants import SERVICE_NAME
from app.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

_HEALTH_HEADERS = {
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow",
}


def _health_payload(*, status: str) -> dict[str, str]:
    return {
        "status": status,
        "service": SERVICE_NAME,
    }


@router.get("/health")
def health_check() -> JSONResponse:
    """Liveness-style probe with a read-only DB ping. No internal details in body."""
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        logger.exception("Health check database probe failed")
        return JSONResponse(
            content=_health_payload(status="degraded"),
            status_code=503,
            headers=_HEALTH_HEADERS,
        )

    return JSONResponse(
        content=_health_payload(status="ok"),
        status_code=200,
        headers=_HEALTH_HEADERS,
    )
