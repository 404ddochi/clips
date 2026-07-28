"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.core.constants import MAIN_NAV
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.security import apply_startup_security_checks
from app.dependencies import get_templates, seo_context
from app.routers import bosses as bosses_router
from app.routers import classes as classes_router
from app.routers import coupons as coupons_router
from app.routers import dev as dev_router
from app.routers import guides as guides_router
from app.routers import health, seo, web
from app.routers import items as items_router
from app.routers import maps as maps_router
from app.routers import news as news_router

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


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
    app = FastAPI(
        title=settings.app_name,
        description="이클립스: 더 어웨이크닝 비공식 정보 플랫폼",
        debug=settings.is_debug_enabled(),
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(health.router)
    app.include_router(seo.router)
    app.include_router(web.router)
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
    templates = get_templates()

    _NOT_FOUND_SHORTCUTS = (
        {"label": "홈", "route_name": "home", "icon": "home"},
        {"label": "소식", "route_name": "news", "icon": "news"},
        {"label": "클래스", "route_name": "classes", "icon": "class"},
        {"label": "아이템", "route_name": "items", "icon": "item"},
        {"label": "보스", "route_name": "bosses", "icon": "boss"},
        {"label": "지도", "route_name": "maps", "icon": "map"},
        {"label": "공략", "route_name": "guides", "icon": "guide"},
        {"label": "쿠폰", "route_name": "coupons", "icon": "coupon"},
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> HTMLResponse:
        if exc.status_code == 404 and _wants_html(request):
            return templates.TemplateResponse(
                request,
                "errors/404.html",
                {
                    "request": request,
                    "status_code": 404,
                    "nav_items": MAIN_NAV,
                    "active_menu": "",
                    "shortcut_links": _NOT_FOUND_SHORTCUTS,
                    **seo_context(
                        title="페이지를 찾을 수 없습니다 - CLIPS",
                        description=(
                            "입력한 주소가 변경되었거나 존재하지 않는 페이지입니다. "
                            "CLIPS 메뉴에서 원하는 정보를 다시 찾아보세요."
                        ),
                        canonical_url=None,
                        robots="noindex, nofollow",
                    ),
                },
                status_code=404,
            )
        if exc.status_code == 404:
            return HTMLResponse(content="Not Found", status_code=404)
        if _wants_html(request):
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
        if _wants_html(request):
            return templates.TemplateResponse(
                request,
                "errors/500.html",
                {
                    "request": request,
                    "status_code": 500,
                    "nav_items": MAIN_NAV,
                    "active_menu": "",
                    **seo_context(
                        title="오류 - CLIPS",
                        description="일시적인 오류가 발생했습니다.",
                        canonical_url=None,
                        robots="noindex, nofollow",
                    ),
                },
                status_code=500,
            )
        return HTMLResponse(content="Internal Server Error", status_code=500)


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept or "*/*" in accept or not accept


app = create_app()
