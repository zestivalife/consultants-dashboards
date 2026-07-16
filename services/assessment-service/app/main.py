import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router
from app.api.v1.routes import health
from app.db.session import dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info(
        "service_starting",
        service=get_settings().app_name,
        routes=[
            {
                "path": getattr(route, "path", None),
                "methods": sorted(getattr(route, "methods", []) or []),
            }
            for route in _app.routes
        ],
    )
    yield
    logger.info("service_shutting_down", service=get_settings().app_name)
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[host.strip() for host in settings.trusted_hosts.split(",") if host.strip()],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if settings.app_env.lower() == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        response.headers["X-Request-Id"] = request_id
        return response

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(health.router)

    return app


app = create_app()
