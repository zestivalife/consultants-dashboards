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

    def ensure_not_reused(self, password: str, previous_hashes: list[str]) -> None:
        for previous_hash in previous_hashes[:5]:
            if previous_hash and self.verify_password(password, previous_hash):
                from app.core.password_policy import WeakPasswordException

                raise WeakPasswordException(["must not match the last 5 passwords"])

    def generate_temporary_password(self, *, prefix: str = "Zestiva") -> str:
        return f"{prefix}@{secrets.token_urlsafe(9)}1"

    def validate_new_password(self, password: str) -> None:
        validate_password(password)


password_service = PasswordService()
