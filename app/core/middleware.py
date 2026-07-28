"""HTTP middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, status, and duration."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers for HTML and API responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        return response


_BLOCKED_DOC_PATHS = frozenset(
    {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"},
)


class ProductionDocsBlockMiddleware(BaseHTTPMiddleware):
    """Hide OpenAPI surfaces when APP_ENV is production (request-time)."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        from app.config import get_settings

        if get_settings().is_production() and request.url.path in _BLOCKED_DOC_PATHS:
            return Response(status_code=404, content="Not Found")
        return await call_next(request)
