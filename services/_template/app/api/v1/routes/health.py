from fastapi import APIRouter
from sqlalchemy import text

from app.core.response import success_response, error_response
from app.db.session import get_engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    return success_response(data={"status": "alive"})


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
    if all_ok:
        return success_response(data={"status": "ready", "checks": checks})
    return error_response(
        message="Service not ready",
        status_code=503,
        errors={"status": "degraded", "checks": checks},
    )
