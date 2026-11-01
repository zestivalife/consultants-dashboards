from dataclasses import dataclass
from typing import Any, Mapping

import httpx


PRACTICE_OPERATIONS_PREFIX = "/api/v1/practice-operations"
PLATFORM_MARKETPLACE_ADMIN_PREFIX = f"{PRACTICE_OPERATIONS_PREFIX}/admin/marketplace"
EXTERNAL_TENANT_TYPES = frozenset({"INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"})
ACTIVE_VALUES = frozenset({"ACTIVE", "READY", "ONBOARDING_IN_PROGRESS"})


class PracticeTenantResolutionError(Exception):
    """A Practice Operations request has no trusted active External tenant."""


@dataclass(frozen=True)
class PracticeTenantAuthority:
    tenant_id: str
    tenant_type: str
    membership_role: str
    profession_hint: str | None = None


def is_practice_operations_path(path: str) -> bool:
    return path == PRACTICE_OPERATIONS_PREFIX or path.startswith(
        PRACTICE_OPERATIONS_PREFIX + "/"
    )


def is_platform_marketplace_admin_path(path: str) -> bool:
    """Platform governance is JWT-authorised, not External-tenant scoped."""
    return path == PLATFORM_MARKETPLACE_ADMIN_PREFIX or path.startswith(
        PLATFORM_MARKETPLACE_ADMIN_PREFIX + "/"
    )


def _canonical_tenant(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise PracticeTenantResolutionError("External tenant authority is unavailable")

    data = payload.get("data")
    authority_source = data if isinstance(data, Mapping) else payload
    authorities = authority_source.get("workspaceAuthorities")
    if isinstance(authorities, list):
        external = [
            item
            for item in authorities
            if isinstance(item, Mapping)
            and str(item.get("tenantType") or "").upper() in EXTERNAL_TENANT_TYPES
            and str(item.get("membershipStatus") or "").upper() == "ACTIVE"
            and str(item.get("resolutionPath") or "").upper() == "MEMBERSHIP"
        ]
        if len(external) == 1:
            return external[0]
        if len(external) > 1:
            raise PracticeTenantResolutionError(
                "Explicit External tenant selection is required"
            )
        raise PracticeTenantResolutionError("No active External membership")
    tenant = payload.get("currentTenant")
    if tenant is None and isinstance(data, Mapping):
        tenant = data.get("currentTenant")
    if not isinstance(tenant, Mapping):
        raise PracticeTenantResolutionError("No active External membership")
    return tenant


def parse_practice_tenant_authority(payload: Any) -> PracticeTenantAuthority:
    """Validate Fiteatsy's canonical, server-selected active membership."""
    tenant = _canonical_tenant(payload)
    tenant_id = str(tenant.get("tenantId") or "").strip()
    tenant_type = str(tenant.get("tenantType") or "").strip().upper()
    membership_role = str(
        tenant.get("currentMembershipRole") or tenant.get("role") or ""
    ).strip().upper()
    resolution_path = str(tenant.get("resolutionPath") or "MEMBERSHIP").strip().upper()
    membership_status = str(tenant.get("membershipStatus") or "ACTIVE").strip().upper()
    tenant_status = str(tenant.get("tenantStatus") or "ACTIVE").strip().upper()

    if not tenant_id or not membership_role or resolution_path != "MEMBERSHIP":
        raise PracticeTenantResolutionError("Invalid External membership authority")
    if tenant_type not in EXTERNAL_TENANT_TYPES:
        raise PracticeTenantResolutionError("Tenant is not an External Practice tenant")
    if membership_status not in ACTIVE_VALUES:
        raise PracticeTenantResolutionError("External membership is inactive")
    if tenant_status not in ACTIVE_VALUES:
        raise PracticeTenantResolutionError("External tenant is inactive")

    return PracticeTenantAuthority(tenant_id, tenant_type, membership_role)


async def resolve_practice_tenant_authority(
    client: httpx.AsyncClient,
    *,
    auth_service_url: str,
    fiteatsy_service_url: str,
    authorization: str | None,
    authenticated_user_id: str | None,
) -> PracticeTenantAuthority:
    if not authenticated_user_id or not authorization or not authorization.startswith("Bearer "):
        raise PracticeTenantResolutionError("Authenticated External identity is required")
    if not auth_service_url:
        raise PracticeTenantResolutionError("External tenant authority is unavailable")

    try:
        response = await client.get(
            f"{auth_service_url.rstrip('/')}/api/v1/auth/me",
            headers={"Authorization": authorization, "Accept": "application/json"},
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise PracticeTenantResolutionError("External tenant authority is unavailable") from exc

    if response.status_code != 200:
        raise PracticeTenantResolutionError("No active External membership")

    try:
        payload = response.json()
    except ValueError as exc:
        raise PracticeTenantResolutionError("External tenant authority is unavailable") from exc
    authority = parse_practice_tenant_authority(payload)

    return PracticeTenantAuthority(
        authority.tenant_id,
        authority.tenant_type,
        authority.membership_role,
        None,
    )
