from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any


SUPPORTED_PROFESSIONS = frozenset({
    "DIABETES_EDUCATOR", "PSYCHOLOGIST", "WELLNESS_CONSULTANT", "HEALTH_COACH",
    "BEHAVIOURAL_THERAPIST", "OCCUPATIONAL_THERAPIST", "PHYSIOTHERAPIST",
    "MENTAL_WELLNESS_THERAPIST",
})
FROZEN_PROFESSIONS = frozenset({"DIETITIAN", "NUTRITIONIST", "DIETITIAN_NUTRITIONIST"})
ALLOWED_ACTIONS = frozenset({"READ", "SAVE", "SUBMIT"})


class IntakeTokenError(ValueError):
    pass


@dataclass(frozen=True)
class IntakeTokenClaims:
    tenant_id: str
    client_id: str
    intake_instance_id: str
    profession_code: str
    template_version_id: str
    allowed_actions: tuple[str, ...]
    expiry: int
    issued_at: int
    token_version: int
    jti: str


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_token(*, secret: str, tenant_id: str, client_id: str, intake_instance_id: str,
                profession_code: str, template_version_id: str, expires_at: int,
                allowed_actions: tuple[str, ...] = ("READ", "SAVE", "SUBMIT"),
                token_version: int = 1, now: int | None = None) -> str:
    actions = tuple(sorted(set(allowed_actions)))
    if not actions or set(actions) - ALLOWED_ACTIONS:
        raise IntakeTokenError("Unsupported profession-intake token action")
    if profession_code not in SUPPORTED_PROFESSIONS:
        raise IntakeTokenError("Unsupported profession")
    issued_at = int(time.time() if now is None else now)
    payload = {
        "aud": "profession-intake", "tenant_id": tenant_id, "client_id": client_id,
        "intake_instance_id": intake_instance_id, "profession_code": profession_code,
        "template_version_id": template_version_id, "allowed_actions": actions,
        "exp": int(expires_at), "iat": issued_at, "token_version": token_version,
        "jti": secrets.token_urlsafe(18),
    }
    encoded = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = _encode(hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest())
    return f"pi1.{encoded}.{signature}"


def validate_token(token: str, *, secret: str, required_action: str, now: int | None = None) -> IntakeTokenClaims:
    if required_action not in ALLOWED_ACTIONS:
        raise IntakeTokenError("Unsupported profession-intake action")
    try:
        prefix, encoded, supplied_signature = token.split(".", 2)
        if prefix != "pi1":
            raise IntakeTokenError("Invalid token version")
        expected = _encode(hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_signature, expected):
            raise IntakeTokenError("Invalid token signature")
        payload: dict[str, Any] = json.loads(_decode(encoded))
    except IntakeTokenError:
        raise
    except Exception as exc:
        raise IntakeTokenError("Invalid profession-intake token") from exc
    if payload.get("aud") != "profession-intake":
        raise IntakeTokenError("Invalid token audience")
    required = ("tenant_id", "client_id", "intake_instance_id", "profession_code", "template_version_id", "jti")
    if any(not isinstance(payload.get(key), str) or not payload[key] for key in required):
        raise IntakeTokenError("Incomplete token scope")
    actions = tuple(payload.get("allowed_actions") or ())
    if required_action not in actions or set(actions) - ALLOWED_ACTIONS:
        raise IntakeTokenError("Token action is not permitted")
    timestamp = int(time.time() if now is None else now)
    if not isinstance(payload.get("exp"), int) or payload["exp"] <= timestamp:
        raise IntakeTokenError("Profession-intake token has expired")
    if payload["profession_code"] not in SUPPORTED_PROFESSIONS:
        raise IntakeTokenError("Unsupported profession")
    return IntakeTokenClaims(
        tenant_id=payload["tenant_id"], client_id=payload["client_id"],
        intake_instance_id=payload["intake_instance_id"], profession_code=payload["profession_code"],
        template_version_id=payload["template_version_id"], allowed_actions=actions,
        expiry=payload["exp"], issued_at=int(payload.get("iat", 0)),
        token_version=int(payload.get("token_version", 0)), jti=payload["jti"],
    )
