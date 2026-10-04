import re

from app.core.exceptions import AppException


def canonical_mobile(value: str) -> str:
    """Return the canonical E.164-style display/storage identity."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        digits = f"91{digits}"
    if not 10 <= len(digits) <= 15:
        raise AppException("Enter a valid mobile number with country code.", 422)
    return f"+{digits}"


def provider_mobile(value: str) -> str:
    """Return the digits-only payload required by the OTP provider."""
    return canonical_mobile(value)[1:]
