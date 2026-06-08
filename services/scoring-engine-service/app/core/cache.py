import json
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_PROFILE_TTL = 600
_ASSESSMENT_TTL = 600

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ── Profile cache ──────────────────────────────────────

async def get_cached_profile(user_id: uuid.UUID) -> dict[str, Any] | None:
    r = await get_redis()
    raw = await r.get(f"profile:{user_id}")
    if raw is not None:
        logger.debug("cache_hit", key=f"profile:{user_id}")
        return json.loads(raw)
    return None


async def set_cached_profile(user_id: uuid.UUID, profile: dict[str, Any]) -> None:
    r = await get_redis()
    await r.setex(f"profile:{user_id}", _PROFILE_TTL, json.dumps(profile))
    logger.debug("cache_set", key=f"profile:{user_id}", ttl=_PROFILE_TTL)


# ── Assessment cache ───────────────────────────────────

async def get_cached_assessments(user_id: uuid.UUID) -> list[dict[str, Any]] | None:
    r = await get_redis()
    raw = await r.get(f"assessment:{user_id}")
    if raw is not None:
        logger.debug("cache_hit", key=f"assessment:{user_id}")
        return json.loads(raw)
    return None


async def set_cached_assessments(user_id: uuid.UUID, responses: list[dict[str, Any]]) -> None:
    r = await get_redis()
    await r.setex(f"assessment:{user_id}", _ASSESSMENT_TTL, json.dumps(responses))
    logger.debug("cache_set", key=f"assessment:{user_id}", ttl=_ASSESSMENT_TTL)


# ── Distributed lock ──────────────────────────────────

_LOCK_TTL = 10

async def acquire_scoring_lock(user_id: uuid.UUID) -> bool:
    r = await get_redis()
    acquired = await r.set(f"scoring_lock:{user_id}", "1", ex=_LOCK_TTL, nx=True)
    if acquired:
        logger.debug("lock_acquired", key=f"scoring_lock:{user_id}")
    return bool(acquired)


async def release_scoring_lock(user_id: uuid.UUID) -> None:
    r = await get_redis()
    await r.delete(f"scoring_lock:{user_id}")
    logger.debug("lock_released", key=f"scoring_lock:{user_id}")
