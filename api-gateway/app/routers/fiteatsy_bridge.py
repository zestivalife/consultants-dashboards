from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.security.fiteatsy_delegation import issue_fiteatsy_delegation

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/platform/fiteatsy")

OPERATIONS: dict[str, tuple[str, str, str]] = {
    "qa-clients": ("POST", "/v1/internal/delegated/qa-clients", "fiteatsy.qa.identity.create"),
    "qa-consultants": ("POST", "/v1/internal/delegated/qa-consultants", "fiteatsy.qa.identity.create"),
    "qa-admins": ("POST", "/v1/internal/delegated/qa-admins", "fiteatsy.qa.admin.create"),
    "client-assignments": ("POST", "/v1/internal/delegated/client-assignments", "fiteatsy.client.assign"),
    "client-assignment-revoke": ("DELETE", "/v1/internal/delegated/client-assignments/{id}", "fiteatsy.client.assignment.revoke"),
    "professional-assignment-clients": ("GET", "/v1/internal/delegated/professional-assignments/clients/pool", "fiteatsy.client.assignment.read"),
    "professional-assignment-professionals": ("GET", "/v1/internal/delegated/professional-assignments/professionals", "fiteatsy.client.assignment.read"),
    "professional-assignments": ("GET", "/v1/internal/delegated/professional-assignments", "fiteatsy.client.assignment.read"),
    "professional-assignment-create": ("POST", "/v1/internal/delegated/professional-assignments", "fiteatsy.client.assign"),
    "professional-assignment-batch": ("POST", "/v1/internal/delegated/professional-assignments/batch", "fiteatsy.client.assign"),
    "professional-assignment-delete": ("DELETE", "/v1/internal/delegated/professional-assignments/{id}", "fiteatsy.client.assignment.revoke"),
    "qa-identities-deactivate": ("POST", "/v1/internal/delegated/qa-identities/{id}/deactivate", "fiteatsy.qa.identity.deactivate"),
}


class QaAdminProvisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=3, max_length=180, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    mobileNumber: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    reason: str = Field(min_length=3, max_length=240)


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
    if role not in {"platform_owner", "super_admin", "superuser"}:
        return None, JSONResponse(status_code=403, content={"error": "OWNER_AUTHORITY_REQUIRED", "message": "Platform Owner authority is required."})
    if not ({"fiteatsy", "fiteatsy-mobile"} & products):
        return None, JSONResponse(status_code=403, content={"error": "FITEATSY_ENTITLEMENT_REQUIRED", "message": "Fiteatsy entitlement is required."})
    if permission and permission.lower() not in permissions:
        return None, JSONResponse(status_code=403, content={"error": "FITEATSY_PERMISSION_REQUIRED", "message": "The requested Fiteatsy operation is not permitted."})
    user_id = getattr(request.state, "user_id", None) or payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        return None, JSONResponse(status_code=403, content={"error": "OWNER_IDENTITY_REQUIRED", "message": "Owner identity is required."})
    return payload, None


async def _bridge(request: Request, operation: str, target_path: str, permission: str, purpose: str, body: dict[str, Any] | None = None, path_params: dict[str, str] | None = None, method: str = "POST", require_operation_permission: bool = True):
    payload, denied = _assert_owner_authority(request, permission if require_operation_permission else "")
    if denied:
        return denied
    settings = get_settings()
    correlation_id = request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id")
    idempotency_key = request.headers.get("Idempotency-Key")
    if method != "GET" and not idempotency_key:
        return JSONResponse(status_code=400, content={"error": "IDEMPOTENCY_KEY_REQUIRED", "message": "Retry-safe operation key is required."})
    path = target_path.format(**(path_params or {}))
    actor_id = str(getattr(request.state, "user_id", None) or payload.get("sub"))
    audit_context = {
        "audit_event": "fiteatsy_delegated_operation",
        "actor_user_id": actor_id,
        "actor_role": "platform_owner",
        "operation": operation,
        "target_system": "fiteatsy",
        "purpose": purpose,
        "permission": permission,
        "correlation_id": correlation_id,
    }
    logger.info("fiteatsy_delegated_operation_requested", **audit_context)
    try:
        delegation = issue_fiteatsy_delegation(subject=actor_id, permissions=[permission], purpose=purpose, actor_type="platform_owner")
    except Exception:
        logger.exception("delegation_issue_failed", operation=operation, correlation_id=correlation_id)
        return JSONResponse(status_code=503, content={"error": "DELEGATION_UNAVAILABLE", "message": "Fiteatsy authority is temporarily unavailable."})
    headers = {"Accept": "application/json", "Content-Type": "application/json", "X-Zestiva-Delegation": delegation, "X-Correlation-Id": correlation_id or ""}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            request_kwargs: dict[str, Any] = {"headers": headers}
            if method == "GET":
                request_kwargs["params"] = dict(request.query_params)
            elif body is not None:
                request_kwargs["json"] = body
            response = await client.request(method, f"{settings.fiteatsy_service_url.rstrip('/')}{path}", **request_kwargs)
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
    response_status = response.status_code
    if response_status == 401:
        logger.error("fiteatsy_delegation_rejected", operation=operation, correlation_id=correlation_id)
        response_status = 502
        response_body = {
            "error": "DOWNSTREAM_AUTHORIZATION_FAILED",
            "message": "Fiteatsy rejected the trusted service delegation. Your Zestiva session remains active; retry after service authorization is restored.",
        }
    logger.info("fiteatsy_delegated_operation_completed", **audit_context, result_status=response.status_code, succeeded=response.is_success)
    return JSONResponse(status_code=response_status, content=response_body)


@router.post("/qa-clients")
async def provision_qa_client(request: Request, body: dict[str, Any]):
    return await _bridge(request, "qa_client_provision", OPERATIONS["qa-clients"][1], OPERATIONS["qa-clients"][2], "qa_provisioning", body)


@router.get("/food-authorisation")
async def list_food_authorisation(request: Request):
    return await _bridge(
        request, "food_authorisation_list", "/v1/internal/delegated/food-authorisation",
        "fiteatsy.food.authorisation.manage", "food_authorisation", method="GET",
        require_operation_permission=False,
    )


@router.get("/leads")
async def list_fiteatsy_leads(request: Request):
    return await _bridge(
        request, "fiteatsy_leads_list", "/v1/internal/delegated/intake-leads",
        "fiteatsy.leads.read", "lead_management", method="GET",
        require_operation_permission=False,
    )


@router.post("/users/{user_id}/temporary-login-pin")
async def issue_fiteatsy_temporary_login_pin(request: Request, user_id: str, body: dict[str, Any]):
    response = await _bridge(
        request, "temporary_login_pin_issue", "/v1/internal/delegated/users/{id}/temporary-login-pin",
        "fiteatsy.login_pin.issue", "login_pin_recovery", body, {"id": user_id},
        require_operation_permission=False,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.post("/food-authorisation/bulk")
async def update_food_authorisation(request: Request, body: dict[str, Any]):
    return await _bridge(
        request, "food_authorisation_bulk_update", "/v1/internal/delegated/food-authorisation/bulk",
        "fiteatsy.food.authorisation.manage", "food_authorisation", body,
        require_operation_permission=False,
    )


@router.post("/qa-consultants")
async def provision_qa_consultant(request: Request, body: dict[str, Any]):
    return await _bridge(request, "qa_consultant_provision", OPERATIONS["qa-consultants"][1], OPERATIONS["qa-consultants"][2], "qa_provisioning", body)


@router.post("/qa-admins")
async def provision_qa_admin(request: Request, body: QaAdminProvisionRequest):
    response = await _bridge(
        request,
        "qa_admin_provision",
        OPERATIONS["qa-admins"][1],
        OPERATIONS["qa-admins"][2],
        "qa_provisioning",
        body.model_dump(),
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.post("/client-assignments")
async def assign_client(request: Request, body: dict[str, Any]):
    return await _bridge(request, "client_assignment", OPERATIONS["client-assignments"][1], OPERATIONS["client-assignments"][2], "client_assignment", body)


@router.delete("/client-assignments/{assignment_id}")
async def revoke_client(request: Request, assignment_id: str):
    return await _bridge(request, "client_assignment_revoke", OPERATIONS["client-assignment-revoke"][1], OPERATIONS["client-assignment-revoke"][2], "client_assignment", {}, {"id": assignment_id}, method="DELETE")


@router.get("/professional-assignments/clients/pool")
async def list_professional_assignment_clients(request: Request):
    operation = OPERATIONS["professional-assignment-clients"]
    return await _bridge(request, "professional_assignment_clients", operation[1], operation[2], "client_assignment", method="GET")


@router.get("/professional-assignments/professionals")
async def list_professional_assignment_professionals(request: Request):
    operation = OPERATIONS["professional-assignment-professionals"]
    return await _bridge(request, "professional_assignment_professionals", operation[1], operation[2], "client_assignment", method="GET")


@router.get("/professional-assignments")
async def list_professional_assignments(request: Request):
    operation = OPERATIONS["professional-assignments"]
    return await _bridge(request, "professional_assignments", operation[1], operation[2], "client_assignment", method="GET")


@router.post("/professional-assignments")
async def create_professional_assignment(request: Request, body: dict[str, Any]):
    operation = OPERATIONS["professional-assignment-create"]
    return await _bridge(request, "professional_assignment_create", operation[1], operation[2], "client_assignment", body)


@router.post("/professional-assignments/batch")
async def create_professional_assignments_batch(request: Request, body: dict[str, Any]):
    operation = OPERATIONS["professional-assignment-batch"]
    return await _bridge(request, "professional_assignment_batch", operation[1], operation[2], "client_assignment", body)


@router.delete("/professional-assignments/{assignment_id}")
async def delete_professional_assignment(request: Request, assignment_id: str, body: dict[str, Any] | None = None):
    operation = OPERATIONS["professional-assignment-delete"]
    return await _bridge(request, "professional_assignment_delete", operation[1], operation[2], "client_assignment", body or {}, {"id": assignment_id}, method="DELETE")


@router.post("/qa-identities/{user_id}/deactivate")
async def deactivate_identity(request: Request, user_id: str, body: dict[str, Any]):
    return await _bridge(request, "qa_identity_deactivate", OPERATIONS["qa-identities-deactivate"][1], OPERATIONS["qa-identities-deactivate"][2], "qa_provisioning", body, {"id": user_id})
