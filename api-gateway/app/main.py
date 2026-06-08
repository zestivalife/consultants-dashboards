import logging
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.config import get_settings
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.jwt import JWTMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.cors import add_cors_middleware
from app.routers.proxy import router as proxy_router, close_http_client

logger = structlog.get_logger(__name__)


def _setup_logging() -> None:
    settings = get_settings()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    _setup_logging()
    settings = get_settings()
    logger.info("gateway_starting", service=settings.app_name)

    # Log all service routes at startup
    routes = settings.get_service_routes()
    for route in routes:
        logger.info("registered_route", prefix=route["prefix"], upstream=route["upstream"])

    yield
    logger.info("gateway_shutting_down")
    await close_http_client()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # Middleware order: outermost runs first.
    # Starlette processes add_middleware in reverse order,
    # so the last added middleware runs first.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(JWTMiddleware)
    add_cors_middleware(app)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/health")
    async def health():
        return {"success": True, "data": {"status": "alive"}}

    @app.get("/ready")
    async def ready():
        return {"success": True, "data": {"status": "ready"}}

    @app.get("/debug/routes")
    async def debug_routes():
        """List all registered service routes for debugging (development only)."""
        routes = settings.get_service_routes()
        return {
            "success": True,
            "data": {
                "service_routes": routes,
                "note": "These are the prefixes that are proxied to upstream services.",
            },
        }

    app.include_router(proxy_router)

    return app


app = create_app()
