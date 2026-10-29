from dataclasses import dataclass
import re
from typing import Any, Mapping

import httpx


PRACTICE_OPERATIONS_PREFIX = "/api/v1/practice-operations"
PLATFORM_MARKETPLACE_ADMIN_PREFIX = f"{PRACTICE_OPERATIONS_PREFIX}/admin/marketplace"
PLATFORM_OWNER_DIRECTORY_PATH = f"{PRACTICE_OPERATIONS_PREFIX}/fiteatsy-client-directory"
PLATFORM_OWNER_ROLES = frozenset({"PLATFORM_OWNER", "SUPERUSER", "SUPER_ADMIN"})
EXTERNAL_TENANT_TYPES = frozenset({"INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"})
ACTIVE_VALUES = frozenset({"ACTIVE", "READY", "ONBOARDING_IN_PROGRESS"})
CLIENT_RESOURCE_PATH = re.compile(
    r"^/api/v1/practice-operations/clients/([^/]+)(?:/|$)"
)


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


def is_platform_owner_directory_path(path: str) -> bool:
    """The canonical Fiteatsy directory is a global Platform Owner resource."""
    return path == PLATFORM_OWNER_DIRECTORY_PATH


def is_platform_owner_role(role: str | None) -> bool:
    return str(role or "").strip().upper() in PLATFORM_OWNER_ROLES


def practice_client_resource_id(path: str) -> str | None:
    match = CLIENT_RESOURCE_PATH.match(path)
    return match.group(1) if match else None


async def client_belongs_to_authenticated_tenant(
    client: httpx.AsyncClient,
    *,
    fiteatsy_service_url: str,
    authorization: str,
    client_id: str,
) -> bool:
    """Use the canonical tenant-scoped client lookup without an existence probe."""
    try:
        response = await client.get(
            f"{fiteatsy_service_url.rstrip('/')}/v1/external/clients/{client_id}",
            headers={"Authorization": authorization, "Accept": "application/json"},
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise PracticeTenantResolutionError("External client authority is unavailable") from exc
    if response.status_code == 200:
        return True
    if response.status_code in {403, 404}:
        return False
    raise PracticeTenantResolutionError("External client authority is unavailable")


def _canonical_tenant(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise PracticeTenantResolutionError("External tenant authority is unavailable")

    data = payload.get("data")
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
    membership_role = str(tenant.get("currentMembershipRole") or "").strip().upper()
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
