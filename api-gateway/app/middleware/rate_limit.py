import redis.asyncio as aioredis

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
import structlog

logger = structlog.get_logger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
            retry_on_timeout=True,
        )
    return _redis


async def is_allowed(key: str, max_requests: int, window_seconds: int = 60) -> bool:
    redis_key = f"gateway_rate_limit:{key}"
    r = await get_redis()
    current = await r.incr(redis_key)
    if current == 1:
        await r.expire(redis_key, window_seconds)
    if current > max_requests:
        logger.warning("gateway_rate_limit_exceeded", key=key, count=current)
        return False
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"user:{user_id}"
        else:
            key = f"ip:{request.client.host if request.client else 'unknown'}"

        try:
            allowed = await is_allowed(key, max_requests=settings.rate_limit_per_minute)
        except Exception as exc:
            logger.error("gateway_rate_limit_check_failed", error=str(exc))
            allowed = True

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded",
                    "data": None,
                    "error": "Too many requests. Please try again later.",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        return await call_next(request)
