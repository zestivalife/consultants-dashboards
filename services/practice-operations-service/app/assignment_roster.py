"""Read-only bridge for the authoritative Fiteatsy assignment roster.

Assignment grants directory visibility only.  It never grants connection or
health-data consent, which remain governed by the existing connection domain.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import httpx
import jwt

from app.config import get_settings


class AssignmentRosterUnavailable(RuntimeError):
    pass


def _delegation(ctx: dict) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    raw_user_id = str(ctx["user_id"])
    canonical_actor = raw_user_id if raw_user_id.startswith("ext_") else f"ext_{UUID(raw_user_id)}"
    claims = {
        "iss": settings.external_fiteatsy_outbound_issuer,
        "sub": canonical_actor,
        "aud": settings.external_fiteatsy_outbound_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=60)).timestamp()),
        "jti": str(uuid4()),
        "product": "fiteatsy",
        "permissions": ["fiteatsy.external.assignment.read"],
        "purpose": "external_consultant_assignment_roster",
        "actor_type": "EXTERNAL_CONSULTANT",
        "tenant_id": str(ctx["tenant_id"]),
    }
    key = (settings.external_fiteatsy_outbound_private_key or "").replace("\\n", "\n")
    return jwt.encode(
        claims,
        key,
        algorithm="RS256",
        headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.external_fiteatsy_outbound_key_id},
    )


async def list_assigned_fiteatsy_clients(ctx: dict) -> list[dict]:
    settings = get_settings()
    backend_url = settings.external_fiteatsy_backend_url
    if not backend_url:
        # The Fiteatsy bridge is optional in isolated/local Practice Operations
        # environments. An explicitly unavailable configured upstream still fails
        # closed below instead of being misreported as an empty roster.
        return []
    url = f"{backend_url.rstrip('/')}/v1/internal/external-consultant-access/assignments/clients"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            upstream = await client.get(url, headers={"x-zestiva-delegation": _delegation(ctx)})
    except (httpx.RequestError, ValueError, TypeError) as exc:
        raise AssignmentRosterUnavailable("The assigned Fiteatsy client roster is temporarily unavailable") from exc
    if upstream.status_code != 200:
        raise AssignmentRosterUnavailable("The assigned Fiteatsy client roster could not be retrieved")
    try:
        clients = upstream.json().get("clients", [])
    except (ValueError, AttributeError) as exc:
        raise AssignmentRosterUnavailable("The assigned Fiteatsy client roster response is invalid") from exc
    if not isinstance(clients, list):
        raise AssignmentRosterUnavailable("The assigned Fiteatsy client roster response is invalid")
    return [client for client in clients if isinstance(client, dict) and client.get("assignmentState") == "ACTIVE"]
