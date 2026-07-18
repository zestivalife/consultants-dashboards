from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_engine
from app.version import get_runtime_version

router = APIRouter(tags=["health"])


async def _get_database_migration_version() -> str:
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            version = result.scalar_one_or_none()
            return str(version) if version else "missing"
    except Exception:
        return "unavailable"


async def _get_runtime_with_database_version(service: str, app_version: str, environment: str) -> dict[str, str]:
    runtime = get_runtime_version(service, app_version, environment)
    runtime["migration_version"] = await _get_database_migration_version()
    return runtime


@router.get("/health")
async def liveness():
    from app.config import get_settings
    settings = get_settings()
    version = await _get_runtime_with_database_version(settings.app_name, settings.app_version, settings.app_env)
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "commit_sha": version["commit_sha"],
        "environment": settings.app_env,
        "runtime": version,
    }


@router.get("/version")
async def version():
    from app.config import get_settings

    settings = get_settings()
    return await _get_runtime_with_database_version(settings.app_name, settings.app_version, settings.app_env)


@router.get("/ready")
async def readiness():
    checks: dict[str, str] = {}

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    try:
        import redis.asyncio as aioredis
        from app.config import get_settings

        settings = get_settings()
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    from app.config import get_settings
    from fastapi.responses import JSONResponse
    settings = get_settings()
    runtime = await _get_runtime_with_database_version(settings.app_name, settings.app_version, settings.app_env)
    if all_ok:
        return {
            "status": "ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "runtime": runtime,
            "checks": checks,
        }
    return JSONResponse(
        status_code=503,
        content={
            "status": "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "runtime": runtime,
            "checks": checks,
        },
    )
