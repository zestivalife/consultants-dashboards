from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_engine
from app.version import get_runtime_version

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    from app.config import get_settings
    settings = get_settings()
    version = get_runtime_version(settings.app_name, settings.app_version, settings.app_env)
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
    return get_runtime_version(settings.app_name, settings.app_version, settings.app_env)


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
    if all_ok:
        return {
            "status": "ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "runtime": get_runtime_version(settings.app_name, settings.app_version, settings.app_env),
            "checks": checks,
        }
    return JSONResponse(
        status_code=503,
        content={
            "status": "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "runtime": get_runtime_version(settings.app_name, settings.app_version, settings.app_env),
            "checks": checks,
        },
    )
