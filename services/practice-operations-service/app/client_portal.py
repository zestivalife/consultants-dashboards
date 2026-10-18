from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass


ALLOWED_ACTIONS = frozenset({"READ", "COMPLETE_TASK", "UPLOAD_DOCUMENT"})


class PortalTokenError(ValueError):
    pass


@dataclass(frozen=True)
class PortalClaims:
    tenant_id: str
    client_id: str
    grant_id: str
    allowed_actions: tuple[str, ...]
    expiry: int
    token_version: int


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def portal_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_portal_token(*, secret: str, tenant_id: str, client_id: str, grant_id: str,
                       expires_at: int, allowed_actions: tuple[str, ...], token_version: int = 1) -> str:
    actions = tuple(sorted(set(allowed_actions)))
    if not actions or set(actions) - ALLOWED_ACTIONS:
        raise PortalTokenError("Unsupported client portal action")
    payload = {
        "aud": "external-client-portal", "tenant_id": tenant_id, "client_id": client_id,
        "grant_id": grant_id, "allowed_actions": actions, "exp": int(expires_at),
        "iat": int(time.time()), "token_version": token_version, "jti": secrets.token_urlsafe(18),
    }
    encoded = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
    return f"cp1.{encoded}.{signature}"


def validate_portal_token(token: str, *, secret: str, required_action: str, now: int | None = None) -> PortalClaims:
    if required_action not in ALLOWED_ACTIONS:
        raise PortalTokenError("Unsupported client portal action")
    try:
        prefix, encoded, supplied = token.split(".", 2)
        if prefix != "cp1":
            raise PortalTokenError("Invalid client portal token")
        expected = _encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied, expected):
            raise PortalTokenError("Invalid client portal token")
        payload = json.loads(_decode(encoded))
    except PortalTokenError:
        raise
    except Exception as exc:
        raise PortalTokenError("Invalid client portal token") from exc
    if payload.get("aud") != "external-client-portal":
        raise PortalTokenError("Invalid client portal token audience")
    actions = tuple(payload.get("allowed_actions") or ())
    if required_action not in actions or set(actions) - ALLOWED_ACTIONS:
        raise PortalTokenError("Client portal action is not permitted")
    timestamp = int(time.time() if now is None else now)
    if not isinstance(payload.get("exp"), int) or payload["exp"] <= timestamp:
        raise PortalTokenError("Client portal link has expired")
    required = ("tenant_id", "client_id", "grant_id")
    if any(not isinstance(payload.get(key), str) or not payload[key] for key in required):
        raise PortalTokenError("Incomplete client portal scope")
    return PortalClaims(
        tenant_id=payload["tenant_id"], client_id=payload["client_id"],
        grant_id=payload["grant_id"], allowed_actions=actions,
        expiry=payload["exp"], token_version=int(payload.get("token_version", 0)),
    )
