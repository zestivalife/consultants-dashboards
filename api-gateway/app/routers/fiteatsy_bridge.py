from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.security.fiteatsy_delegation import issue_fiteatsy_delegation

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/platform/fiteatsy")

OPERATIONS: dict[str, tuple[str, str, str]] = {
    "qa-clients": ("POST", "/v1/internal/delegated/qa-clients", "fiteatsy.qa.identity.create"),
    "qa-consultants": ("POST", "/v1/internal/delegated/qa-consultants", "fiteatsy.qa.identity.create"),
    "client-assignments": ("POST", "/v1/internal/delegated/client-assignments", "fiteatsy.client.assign"),
    "client-assignment-revoke": ("DELETE", "/v1/internal/delegated/client-assignments/{id}", "fiteatsy.client.assignment.revoke"),
    "qa-identities-deactivate": ("POST", "/v1/internal/delegated/qa-identities/{id}/deactivate", "fiteatsy.qa.identity.deactivate"),
    "qa-session": ("POST", "/v1/internal/delegated/qa-identities/{id}/session", "fiteatsy.qa.session.issue"),
}


def _claim_values(payload: dict[str, Any], names: tuple[str, ...]) -> set[str]:
    values: set[str] = set()
    for name in names:
        value = payload.get(name)
        if isinstance(value, str):
            values.add(value.strip().lower())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    values.add(item.strip().lower())
                elif isinstance(item, dict):
                    for key in ("key", "id", "name", "product", "product_id"):
                        if isinstance(item.get(key), str):
                            values.add(item[key].strip().lower())
    return values


def _assert_owner_authority(request: Request, permission: str) -> tuple[dict[str, Any] | None, JSONResponse | None]:
    payload = getattr(request.state, "token_payload", {}) or {}
    role = str(getattr(request.state, "user_role", "") or payload.get("role") or "").lower()
    permissions = _claim_values(payload, ("permissions", "permission", "scopes"))
    products = _claim_values(payload, ("products", "product_entitlements", "entitlements", "product"))
    if role != "platform_owner":
        return None, JSONResponse(status_code=403, content={"error": "OWNER_AUTHORITY_REQUIRED", "message": "Platform Owner authority is required."})
    if not ({"fiteatsy", "fiteatsy-mobile"} & products):
        return None, JSONResponse(status_code=403, content={"error": "FITEATSY_ENTITLEMENT_REQUIRED", "message": "Fiteatsy entitlement is required."})
    if permission.lower() not in permissions:
        return None, JSONResponse(status_code=403, content={"error": "FITEATSY_PERMISSION_REQUIRED", "message": "The requested Fiteatsy operation is not permitted."})
    user_id = getattr(request.state, "user_id", None) or payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        return None, JSONResponse(status_code=403, content={"error": "OWNER_IDENTITY_REQUIRED", "message": "Owner identity is required."})
    return payload, None


async def _bridge(request: Request, operation: str, target_path: str, permission: str, purpose: str, body: dict[str, Any], path_params: dict[str, str] | None = None, method: str = "POST"):
    payload, denied = _assert_owner_authority(request, permission)
    if denied:
        return denied
    settings = get_settings()
    correlation_id = request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id")
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return JSONResponse(status_code=400, content={"error": "IDEMPOTENCY_KEY_REQUIRED", "message": "Retry-safe operation key is required."})
    path = target_path.format(**(path_params or {}))
    try:
        delegation = issue_fiteatsy_delegation(subject=str(getattr(request.state, "user_id", None) or payload.get("sub")), permissions=[permission], purpose=purpose, actor_type="platform_owner")
    except Exception:
        logger.exception("delegation_issue_failed", operation=operation, correlation_id=correlation_id)
        return JSONResponse(status_code=503, content={"error": "DELEGATION_UNAVAILABLE", "message": "Fiteatsy authority is temporarily unavailable."})
    headers = {"Accept": "application/json", "Content-Type": "application/json", "X-Zestiva-Delegation": delegation, "X-Correlation-Id": correlation_id or "", "Idempotency-Key": idempotency_key}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            response = await client.request(method, f"{settings.fiteatsy_service_url.rstrip('/')}{path}", headers=headers, json=body)
    except httpx.TimeoutException:
        logger.warning("fiteatsy_bridge_timeout", operation=operation, correlation_id=correlation_id)
        return JSONResponse(status_code=504, content={"error": "FITEATSY_TIMEOUT", "message": "Fiteatsy did not respond in time."})
    except httpx.HTTPError:
        logger.exception("fiteatsy_bridge_unavailable", operation=operation, correlation_id=correlation_id)
        return JSONResponse(status_code=502, content={"error": "FITEATSY_UNAVAILABLE", "message": "Fiteatsy is temporarily unavailable."})
    try:
        response_body = response.json()
    except ValueError:
        response_body = {"error": "FITEATSY_INVALID_RESPONSE"}
    logger.info("fiteatsy_bridge_completed", operation=operation, permission=permission, purpose=purpose, correlation_id=correlation_id, status=response.status_code)
    return JSONResponse(status_code=response.status_code, content=response_body)


@router.post("/qa-clients")
async def provision_qa_client(request: Request, body: dict[str, Any]):
    return await _bridge(request, "qa_client_provision", OPERATIONS["qa-clients"][1], OPERATIONS["qa-clients"][2], "qa_provisioning", body)


@router.post("/qa-consultants")
async def provision_qa_consultant(request: Request, body: dict[str, Any]):
    return await _bridge(request, "qa_consultant_provision", OPERATIONS["qa-consultants"][1], OPERATIONS["qa-consultants"][2], "qa_provisioning", body)


@router.post("/client-assignments")
async def assign_client(request: Request, body: dict[str, Any]):
    return await _bridge(request, "client_assignment", OPERATIONS["client-assignments"][1], OPERATIONS["client-assignments"][2], "client_assignment", body)


@router.delete("/client-assignments/{assignment_id}")
async def revoke_client(request: Request, assignment_id: str):
    return await _bridge(request, "client_assignment_revoke", OPERATIONS["client-assignment-revoke"][1], OPERATIONS["client-assignment-revoke"][2], "client_assignment", {}, {"id": assignment_id}, method="DELETE")


@router.post("/qa-identities/{user_id}/deactivate")
async def deactivate_identity(request: Request, user_id: str, body: dict[str, Any]):
    return await _bridge(request, "qa_identity_deactivate", OPERATIONS["qa-identities-deactivate"][1], OPERATIONS["qa-identities-deactivate"][2], "qa_provisioning", body, {"id": user_id})


@router.post("/qa-identities/{user_id}/session")
async def issue_session(request: Request, user_id: str, body: dict[str, Any]):
    return await _bridge(request, "qa_session_issue", OPERATIONS["qa-session"][1], OPERATIONS["qa-session"][2], "qa_session", body, {"id": user_id})
