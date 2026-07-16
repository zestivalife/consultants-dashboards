import logging
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import httpx
import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.jwt import JWTMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.cors import add_cors_middleware
from app.routers.proxy import router as proxy_router, close_http_client
from app.version import get_runtime_version

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
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[host.strip() for host in settings.trusted_hosts.split(",") if host.strip()],
    )
    app.add_middleware(RequestIdMiddleware)

    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if settings.app_env.lower() == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        return response

    @app.get("/health")
    async def health():
        version = get_runtime_version(settings.app_name, settings.app_version, settings.app_env)
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "commit_sha": version["commit_sha"],
            "environment": settings.app_env,
            "runtime": version,
        }

    @app.get("/version")
    async def version():
        return get_runtime_version(settings.app_name, settings.app_version, settings.app_env)

    @app.get("/api/v1/version")
    async def api_version():
        return get_runtime_version(settings.app_name, settings.app_version, settings.app_env)

    @app.get("/api/v1/versions")
    async def service_versions():
        gateway_version = get_runtime_version(settings.app_name, settings.app_version, settings.app_env)
        services: dict[str, dict | str] = {"api-gateway": gateway_version}

        upstreams = settings.get_service_upstreams()

        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
            for label, upstream in sorted(upstreams.items()):
                try:
                    response = await client.get(f"{upstream}/api/v1/version")
                    services[label] = response.json() if response.status_code == 200 else {
                        "status": "unavailable",
                        "http_status": response.status_code,
                    }
                except Exception as exc:
                    services[label] = {
                        "status": "unavailable",
                        "error": str(exc),
                    }

        return {
            "status": "ok",
            "environment": settings.app_env,
            "services": services,
        }

    @app.get("/ready")
    async def ready():
        checks: dict[str, str] = {}

        try:
            r = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"

        routes = settings.get_service_routes()
        upstreams = {route["upstream"] for route in routes}
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
            for upstream in sorted(upstreams):
                service_name = upstream.rsplit("/", 1)[-1]
                try:
                    response = await client.get(f"{upstream}/api/v1/health")
                    checks[service_name] = "ok" if response.status_code == 200 else "unavailable"
                except Exception:
                    checks[service_name] = "unavailable"

        all_ok = all(value == "ok" for value in checks.values())
        body = {
            "status": "ready" if all_ok else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "runtime": get_runtime_version(settings.app_name, settings.app_version, settings.app_env),
            "checks": checks,
        }
        if all_ok:
            return body
        return JSONResponse(status_code=503, content=body)

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
