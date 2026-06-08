import re

from app.core.exceptions import AppException


class WeakPasswordException(AppException):
    def __init__(self, reasons: list[str]):
        message = "Password does not meet requirements: " + "; ".join(reasons)
        super().__init__(message=message, status_code=422)
        self.reasons = reasons


def validate_password(password: str) -> None:
    """Enforce password strength rules. Raises WeakPasswordException on failure."""
    reasons: list[str] = []

    if len(password) < 8:
        reasons.append("minimum 8 characters")
    if not re.search(r"[A-Z]", password):
        reasons.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        reasons.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        reasons.append("at least one digit")

    if reasons:
        raise WeakPasswordException(reasons)
