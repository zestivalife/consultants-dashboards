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
from app.db.session import dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    settings = get_settings()
    logger.info("service_starting", service=settings.app_name, env=settings.app_env)

    # ── Eagerly initialise email service so provider selection is logged at startup ──
    # This way "email_provider_init provider=SendGrid mode=explicit" appears in logs
    # immediately rather than waiting for the first email to be sent.
    from app.core.email import get_email_service
    try:
        svc = get_email_service()
        logger.info(
            "email_service_ready",
            provider=type(svc._provider).__name__,
            email_provider_setting=settings.email_provider,
            sendgrid_key_present=bool(settings.sendgrid_api_key),
            from_email=settings.smtp_from_email,
        )
    except Exception as exc:
        logger.error("email_service_init_failed", error=str(exc))

    yield

    logger.info("service_shutting_down", service=settings.app_name)
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        # Always expose docs — makes /test-email discoverable in Swagger
        docs_url="/docs",
        redoc_url="/redoc",
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

    return app


app = create_app()
