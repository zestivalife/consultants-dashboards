from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Header

from app.config import get_settings


class OwnerProfessionDelegationError(Exception):
    pass


@dataclass(frozen=True)
class OwnerProfessionDelegation:
    actor_id: str
    user_id: str
    tenant_id: str


def require_owner_profession_delegation(
    x_owner_delegation: str | None = Header(default=None),
) -> OwnerProfessionDelegation:
    settings = get_settings()
    if not x_owner_delegation or not settings.qa_delegation_public_key:
        raise OwnerProfessionDelegationError("Signed Owner Console delegation is required")
    try:
        payload: dict[str, Any] = jwt.decode(
            x_owner_delegation, settings.qa_delegation_public_key.replace("\\n", "\n"),
            algorithms=["RS256"], audience=settings.qa_delegation_audience,
            issuer=settings.qa_delegation_issuer, options={"require": ["exp", "iat", "jti", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise OwnerProfessionDelegationError("Signed Owner Console delegation is invalid") from exc
    if payload.get("purpose") != "owner_profession_configuration" or payload.get("actor_type") != "platform_owner":
        raise OwnerProfessionDelegationError("Owner Console delegation purpose is invalid")
    if "practice.owner.profession.manage" not in (payload.get("permissions") or []):
        raise OwnerProfessionDelegationError("Owner Console profession permission is missing")
    claims = [payload.get(name) for name in ("sub", "target_user_id", "tenant_id")]
    if not all(isinstance(value, str) and value for value in claims):
        raise OwnerProfessionDelegationError("Owner Console profession scope is incomplete")
    return OwnerProfessionDelegation(*claims)
