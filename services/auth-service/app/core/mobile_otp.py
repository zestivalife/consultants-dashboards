import httpx

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.core.mobile_identity import provider_mobile

logger = get_logger(__name__)


async def send_mobile_otp(mobile: str, code: str) -> None:
    settings = get_settings()
    recipient = provider_mobile(mobile)
    if settings.app_env.lower() == "test":
        logger.info("consultant_otp_delivery_skipped", provider="test-noop")
        return
    if not settings.pingmate_api_key:
        logger.error("consultant_otp_provider_unavailable", provider="pingmate", reason="missing_api_key")
        raise AppException("Unable to send OTP. Please try again.", 503)
    base_url = settings.pingmate_base_url.rstrip("/")
    request_url = base_url if base_url.endswith("/messages/send") else f"{base_url}/messages/send"
    payload = {
        "to": recipient,
        "message": {
            "message_type": "template",
            "template_name": settings.pingmate_template,
            "template_language": settings.pingmate_language,
            "body_variables": [code],
            "buttons": [{"button_type": "url", "button_index": 0, "button_payload": code}],
        },
    }
    logger.info(
        "consultant_otp_request",
        provider="pingmate",
        recipient_format="digits_only",
        recipient_length=len(recipient),
        template=settings.pingmate_template,
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                request_url,
                headers={"Content-Type": "application/json", "X-API-Key": settings.pingmate_api_key},
                json=payload,
            )
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        logger.warning("consultant_otp_delivery_failed", provider="pingmate", failure=type(exc).__name__)
        raise AppException("Unable to send OTP. Please try again.", 503) from exc
    if not response.is_success:
        logger.warning("consultant_otp_delivery_failed", provider="pingmate", status_code=response.status_code)
        raise AppException("Unable to send OTP. Please try again.", 503)
    logger.info("consultant_otp_delivered", provider="pingmate", status_code=response.status_code)
