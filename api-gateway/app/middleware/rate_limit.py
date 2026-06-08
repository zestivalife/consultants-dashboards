import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings


class InMemoryRateLimiter:
    """Simple sliding-window rate limiter. Swap for Redis-backed version in production clusters."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        hits = self._hits[key] = [t for t in self._hits[key] if t > cutoff]
        if len(hits) >= max_requests:
            return False
        hits.append(now)
        return True


_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"user:{user_id}"
        else:
            key = f"ip:{request.client.host if request.client else 'unknown'}"

        if not _limiter.is_allowed(key, max_requests=settings.rate_limit_per_minute):
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
