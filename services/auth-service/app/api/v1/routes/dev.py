"""
DEV-ONLY routes — NOT for production use.
Expose OTP fetched from Redis so developers can test without SMTP.
"""
from fastapi import APIRouter, Query
from app.core.otp import _get_redis
from app.config import get_settings
from app.core.response import success_response
from fastapi.responses import JSONResponse

router = APIRouter(tags=["dev"])


@router.get("/otp")
async def get_dev_otp(email: str = Query(..., description="Email to fetch OTP for")):
    """
    DEV ONLY: Retrieve the current OTP for an email from Redis.
    Remove this endpoint before going to production.
    """
    settings = get_settings()
    if settings.app_env != "development":
        return JSONResponse(status_code=403, content={"error": "Not available in production"})

    r = await _get_redis()
    try:
        otp = await r.get(f"otp:{email}")
        ttl = await r.ttl(f"otp:{email}")
    finally:
        await r.aclose()

    if otp is None:
        return JSONResponse(status_code=404, content={"error": "No OTP found for this email. It may have expired."})

    return success_response(
        data={"email": email, "otp": otp, "expires_in_seconds": ttl},
        message="[DEV] OTP retrieved from Redis",
    )
