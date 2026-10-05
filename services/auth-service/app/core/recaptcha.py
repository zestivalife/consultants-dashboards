import httpx

from app.config import get_settings
from app.core.exceptions import AppException


async def verify_recaptcha(token: str, remote_ip: str | None = None) -> None:
    settings = get_settings()
    if settings.app_env.lower() == "test" and token == "test-recaptcha-token":
        return
    if not settings.recaptcha_secret_key:
        raise AppException("Consultant registration is temporarily unavailable.", 503)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.recaptcha_verify_url,
                data={"secret": settings.recaptcha_secret_key, "response": token, "remoteip": remote_ip},
            )
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise AppException("CAPTCHA verification could not be completed.", 503) from exc
    if not result.get("success"):
        raise AppException("Complete the CAPTCHA and try again.", 422)
    expected_hostname = settings.recaptcha_expected_hostname
    if expected_hostname and result.get("hostname") != expected_hostname:
        raise AppException("CAPTCHA verification is invalid for this site.", 422)
