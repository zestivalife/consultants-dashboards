import random

import redis.asyncio as aioredis

from app.config import get_settings


async def _get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def generate_otp() -> str:
    return str(random.randint(100_000, 999_999))


async def store_otp(email: str, code: str) -> None:
    settings = get_settings()
    r = await _get_redis()
    try:
        await r.setex(f"otp:{email}", settings.otp_expiry_seconds, code)
    finally:
        await r.aclose()


async def verify_and_delete_otp(email: str, code: str) -> bool:
    r = await _get_redis()
    try:
        stored = await r.get(f"otp:{email}")
        if stored is None or stored != code:
            return False
        await r.delete(f"otp:{email}")
        return True
    finally:
        await r.aclose()
