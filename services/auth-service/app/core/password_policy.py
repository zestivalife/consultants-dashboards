import re

from app.core.exceptions import AppException

COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "password123!",
    "qwerty123",
    "qwerty123!",
    "admin123",
    "admin123!",
    "welcome123",
    "welcome123!",
    "zestiva123",
    "zestiva123!",
}


class WeakPasswordException(AppException):
    def __init__(self, reasons: list[str]):
        message = "Password does not meet requirements: " + "; ".join(reasons)
        super().__init__(message=message, status_code=422)
        self.reasons = reasons


def validate_password(password: str) -> None:
    """Enforce password strength rules. Raises WeakPasswordException on failure."""
    reasons: list[str] = []

    if len(password) < 12:
        reasons.append("minimum 12 characters")
    if not re.search(r"[A-Z]", password):
        reasons.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        reasons.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        reasons.append("at least one digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        reasons.append("at least one special character")
    if password.strip().lower() in COMMON_PASSWORDS:
        reasons.append("not a commonly used password")

    if reasons:
        raise WeakPasswordException(reasons)
