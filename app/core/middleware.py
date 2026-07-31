"""HTTP middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# Clickjacking: app does not embed itself in iframes.
X_FRAME_OPTIONS = "DENY"

X_CONTENT_TYPE_OPTIONS = "nosniff"
REFERRER_POLICY = "strict-origin-when-cross-origin"

# Do not restrict clipboard-* (coupon copy) or fullscreen.
PERMISSIONS_POLICY = (
    "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
    "accelerometer=(), gyroscope=(), magnetometer=(), interest-cohort=()"
)

# Report-Only only — no enforce header until nonce/hash lands.
_CSP_REPORT_ONLY_DIRECTIVES: tuple[str, ...] = (
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com",
    "style-src 'self' 'unsafe-inline'",
    (
        "img-src 'self' data: https://www.google-analytics.com "
        "https://www.googletagmanager.com"
    ),
    "font-src 'self'",
    (
        "connect-src 'self' https://www.google-analytics.com "
        "https://analytics.google.com https://region1.google-analytics.com "
        "https://www.googletagmanager.com"
    ),
    "manifest-src 'self'",
    "worker-src 'none'",
    "frame-src 'none'",
    "media-src 'self'",
)

CONTENT_SECURITY_POLICY_REPORT_ONLY = "; ".join(_CSP_REPORT_ONLY_DIRECTIVES)


def apply_security_headers[ResponseT: Response](response: ResponseT) -> ResponseT:
    """Set baseline security headers on a Response (setdefault)."""
    response.headers.setdefault("X-Content-Type-Options", X_CONTENT_TYPE_OPTIONS)
    response.headers.setdefault("X-Frame-Options", X_FRAME_OPTIONS)
    response.headers.setdefault("Referrer-Policy", REFERRER_POLICY)
    response.headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
    response.headers.setdefault(
        "Content-Security-Policy-Report-Only",
        CONTENT_SECURITY_POLICY_REPORT_ONLY,
    )
    return response


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


class SecurityHeadersMiddleware:
    """Attach baseline security headers to every HTTP response (ASGI).

    Pure ASGI middleware injects headers on ``http.response.start``.
    Error page builders also call ``apply_security_headers`` because
    BaseHTTPMiddleware can re-raise after ExceptionMiddleware has already
    produced a branded 500, skipping outer header mutation in some paths.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", X_CONTENT_TYPE_OPTIONS)
                headers.setdefault("X-Frame-Options", X_FRAME_OPTIONS)
                headers.setdefault("Referrer-Policy", REFERRER_POLICY)
                headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
                headers.setdefault(
                    "Content-Security-Policy-Report-Only",
                    CONTENT_SECURITY_POLICY_REPORT_ONLY,
                )
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


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
        from app.core.error_pages import not_found_response

        if get_settings().is_production() and request.url.path in _BLOCKED_DOC_PATHS:
            # Shared branded/plain 404 (same as exception handler); avoid raising
            # inside BaseHTTPMiddleware which may bypass exception handlers.
            return not_found_response(request)
        return await call_next(request)
