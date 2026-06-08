import uuid
from typing import Any

import httpx

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0))
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def fetch_profile(user_id: uuid.UUID, request_id: str | None = None) -> dict[str, Any] | None:
    settings = get_settings()
    url = f"{settings.profile_service_url}/api/v1/profile/me"
    headers: dict[str, str] = {"X-User-Id": str(user_id)}
    if request_id:
        headers["X-Request-Id"] = request_id

    client = await get_client()
    try:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            body = resp.json()
            return body.get("data")
        logger.warning("profile_fetch_failed", status=resp.status_code, user_id=str(user_id))
        return None
    except httpx.HTTPError as exc:
        logger.error("profile_fetch_error", error=str(exc))
        return None


async def fetch_assessment_history(
    user_id: uuid.UUID,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    url = f"{settings.assessment_service_url}/api/v1/assessments/history"
    headers: dict[str, str] = {"X-User-Id": str(user_id)}
    if request_id:
        headers["X-Request-Id"] = request_id

    client = await get_client()
    try:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            body = resp.json()
            data = body.get("data", {})
            return data.get("submissions", [])
        return []
    except httpx.HTTPError as exc:
        logger.error("assessment_fetch_error", error=str(exc))
        return []
