"""Security helpers."""

from __future__ import annotations

import logging

from app.config import Settings, validate_settings

logger = logging.getLogger(__name__)


def apply_startup_security_checks(settings: Settings) -> None:
    validate_settings(settings)
    if not settings.is_production() and settings.secret_key == "change-me":
        logger.warning("SECRET_KEY가 기본값입니다. 운영 배포 전 반드시 변경하세요.")
