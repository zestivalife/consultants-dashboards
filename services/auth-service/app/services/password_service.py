import secrets

from app.core.password_policy import validate_password
from app.core.security import hash_password as _hash_password
from app.core.security import verify_password as _verify_password


class PasswordService:
    """Single application boundary for password lifecycle operations."""

    def hash_password(self, password: str, *, validate: bool = True) -> str:
        if validate:
            validate_password(password)
        return _hash_password(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return _verify_password(plain, hashed)

    def generate_temporary_password(self, *, prefix: str = "Zestiva") -> str:
        return f"{prefix}@{secrets.token_urlsafe(9)}1"

    def validate_new_password(self, password: str) -> None:
        validate_password(password)


password_service = PasswordService()
