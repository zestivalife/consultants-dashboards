from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Header

from app.config import get_settings


class QaDelegationError(Exception):
    pass


@dataclass(frozen=True)
class QaDelegation:
    actor_id: str
    user_id: str
    tenant_id: str
    profession_code: str


def require_qa_delegation(x_qa_delegation: str | None = Header(default=None)) -> QaDelegation:
    settings = get_settings()
    if not x_qa_delegation or not settings.qa_delegation_public_key:
        raise QaDelegationError("Signed QA delegation is required")
    try:
        payload: dict[str, Any] = jwt.decode(
            x_qa_delegation, settings.qa_delegation_public_key.replace("\\n", "\n"),
            algorithms=["RS256"], audience=settings.qa_delegation_audience,
            issuer=settings.qa_delegation_issuer, options={"require": ["exp", "iat", "jti", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise QaDelegationError("Signed QA delegation is invalid") from exc
    if payload.get("purpose") != "qa_external_practice" or payload.get("actor_type") != "platform_owner":
        raise QaDelegationError("QA delegation purpose is invalid")
    if "practice.qa.external.configure" not in (payload.get("permissions") or []):
        raise QaDelegationError("QA delegation permission is missing")
    claims = [payload.get(name) for name in ("sub", "target_user_id", "tenant_id", "profession_code")]
    if not all(isinstance(value, str) and value for value in claims):
        raise QaDelegationError("QA delegation scope is incomplete")
    return QaDelegation(*claims)
