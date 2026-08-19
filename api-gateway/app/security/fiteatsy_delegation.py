"""Issuer for short-lived Zestiva -> Fiteatsy server authority."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.config import get_settings


class DelegationConfigurationError(RuntimeError):
    pass


def issue_fiteatsy_delegation(
    *,
    subject: str,
    permissions: list[str],
    purpose: str,
    actor_type: str,
    tenant_id: str | None = None,
) -> str:
    settings = get_settings()
    if not settings.fiteatsy_delegation_private_key or not settings.fiteatsy_delegation_key_id:
        raise DelegationConfigurationError("Fiteatsy delegation signing configuration is incomplete")
    if not subject.strip() or not permissions or not purpose.strip() or not actor_type.strip():
        raise ValueError("Delegation subject, permissions, purpose, and actor_type are required")

    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.fiteatsy_delegation_issuer,
        "sub": subject,
        "aud": settings.fiteatsy_delegation_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.fiteatsy_delegation_ttl_seconds)).timestamp()),
        "jti": str(uuid4()),
        "product": "fiteatsy",
        "permissions": sorted(set(permissions)),
        "purpose": purpose,
        "actor_type": actor_type,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return jwt.encode(
        payload,
        settings.fiteatsy_delegation_private_key.replace("\\n", "\n"),
        algorithm="RS256",
        headers={"kid": settings.fiteatsy_delegation_key_id, "typ": "Zestiva-Delegated-Authority"},
    )
