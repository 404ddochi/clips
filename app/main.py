"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.core.error_pages import not_found_response, server_error_response, wants_html
from app.core.logging import configure_logging
from app.core.middleware import (
    ProductionDocsBlockMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.security import apply_startup_security_checks
from app.routers import bosses as bosses_router
from app.routers import classes as classes_router
from app.routers import coupons as coupons_router
from app.routers import dev as dev_router
from app.routers import guides as guides_router
from app.routers import health, seo, web
from app.routers import items as items_router
from app.routers import maps as maps_router
from app.routers import news as news_router
from app.routers import search as search_router

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

# Ensure StaticFiles serves PWA / favicon types correctly on all platforms.
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("image/x-icon", ".ico")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.is_debug_enabled())
    apply_startup_security_checks(settings)
    logger.info("CLIPS starting (env=%s, debug=%s)", settings.app_env, settings.app_debug)
    yield
    logger.info("CLIPS shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    docs_enabled = not settings.is_production()
    app = FastAPI(
        title=settings.app_name,
        description="이클립스: 더 어웨이크닝 비공식 정보 플랫폼",
        debug=settings.is_debug_enabled(),
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    # Last added runs outermost. Security headers must wrap all sends
    # (including ExceptionMiddleware error responses).
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ProductionDocsBlockMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(health.router)
    app.include_router(seo.router)
    app.include_router(web.router)
    app.include_router(search_router.router)
    app.include_router(classes_router.router)
    app.include_router(bosses_router.router)
    app.include_router(items_router.router)
    app.include_router(maps_router.router)
    app.include_router(guides_router.router)
    app.include_router(news_router.router)
    app.include_router(coupons_router.router)
    app.include_router(dev_router.router)

    register_exception_handlers(app)
    return app


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> HTMLResponse:
        if exc.status_code == 404:
            return not_found_response(request)
        if wants_html(request):
            return HTMLResponse(
                content=str(exc.detail),
                status_code=exc.status_code,
            )
        raise exc

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> HTMLResponse:
        logger.exception("Unhandled error: %s", exc)
        return server_error_response(request)


app = create_app()
