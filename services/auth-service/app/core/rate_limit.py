import redis.asyncio as aioredis

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def _get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def check_rate_limit(key: str) -> bool:
    """Return True if the request is allowed, False if rate-limited.

    Uses a sliding-window counter in Redis: key = rate_limit:{scope}:{identifier}.
    """
    settings = get_settings()
    max_requests = settings.login_rate_limit_max
    window = settings.login_rate_limit_window_seconds

    r = await _get_redis()
    try:
        redis_key = f"rate_limit:{key}"
        current = await r.incr(redis_key)
        if current == 1:
            await r.expire(redis_key, window)
        if current > max_requests:
            logger.warning("rate_limit_exceeded", key=key, count=current)
            return False
        return True
    finally:
        await r.aclose()
