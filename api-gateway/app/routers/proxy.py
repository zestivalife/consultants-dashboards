import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from urllib.parse import urlsplit

from app.config import get_settings
from app.routers.owner_permissions import required_owner_permissions
from app.routers.practice_tenant_resolver import (
    PracticeTenantResolutionError,
    client_belongs_to_authenticated_tenant,
    is_practice_operations_path,
    is_platform_marketplace_admin_path,
    is_platform_owner_directory_path,
    is_platform_owner_role,
    practice_client_resource_id,
    resolve_practice_tenant_authority,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

_client: httpx.AsyncClient | None = None

DELEGATED_PERMISSION_PREFIXES: tuple[str, ...] = (
    "/api/v1/owner/people-access",
    "/api/v1/owner/master-data",
)

INTERNAL_PROFILE_PREFIX = "/api/v1/practice-operations/internal-client-profiles"
LEGACY_SIMULATED_REPORT_PATH = "/api/v1/profile/upload-report"
EXTERNAL_TENANT_TYPES = {"INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"}


async def _internal_client_visible(client: httpx.AsyncClient, service_url: str, authorization: str, client_id: str) -> bool:
    """Re-use the canonical read-only Internal workspace lookup as the access decision."""
    try:
        response = await client.get(
            f"{service_url.rstrip('/')}/v1/consultants/clients/{client_id}/workspace",
            headers={"Authorization": authorization, "Accept": "application/json"},
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise PracticeTenantResolutionError("Internal client authority is unavailable") from exc
    if response.status_code == 200:
        return True
    if response.status_code in {403, 404}:
        return False
    raise PracticeTenantResolutionError("Internal client authority is unavailable")

async def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _resolve_upstream(path: str) -> tuple[str, str, str | None] | None:
    """Match the request path to an upstream service URL."""
    settings = get_settings()
    routes = settings.get_service_routes()
    for route in routes:
        prefix = route["prefix"]
        if path == prefix or path.startswith(prefix + "/"):
            remaining = path[len(prefix):]
            logger.debug("route_match_success", path=path, prefix=prefix, upstream=route["upstream"])
            return route["upstream"], remaining, route.get("host_header")
    logger.warning("route_match_failure", path=path)
    return None


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy(request: Request, path: str):
    full_path = f"/{path}"
    tenant_type = str(getattr(request.state, "tenant_type", "") or "").upper()
    if full_path == LEGACY_SIMULATED_REPORT_PATH and tenant_type in EXTERNAL_TENANT_TYPES:
        logger.warning(
            "legacy_simulated_report_path_blocked",
            path=full_path,
            tenant_type=tenant_type,
            mutation_performed=False,
        )
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Clinical extraction is unavailable on this legacy endpoint. Use External Health Records.",
                "data": None,
                "error": "CLINICAL_EXTRACTION_UNAVAILABLE",
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    required_permissions = required_owner_permissions(full_path, request.method.upper())
    user_permissions = set(getattr(request.state, "user_permissions", []) or [])
    delegated_permissions = any(
        full_path == prefix or full_path.startswith(prefix + "/")
        for prefix in DELEGATED_PERMISSION_PREFIXES
    )
    if required_permissions and not delegated_permissions and not (user_permissions & required_permissions):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "You do not have permission to access this resource",
                "data": None,
                "error": "Forbidden",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    resolved = _resolve_upstream(full_path)

    if resolved is None:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": f"No upstream service for path: {full_path}",
                "data": None,
                "error": "Route not found",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    upstream_base, _, host_header = resolved
    target_url = f"{upstream_base}{full_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    headers = dict(request.headers)
    headers.pop("host", None)
    # Authority headers are gateway-owned and must never be accepted from callers.
    for authority_header in ("x-user-id", "x-user-role", "x-user-permissions", "x-tenant-id", "x-tenant-type", "x-profession-code"):
        headers.pop(authority_header, None)
    upstream_host = urlsplit(upstream_base).hostname or ""
    if upstream_host.endswith(".railway.internal"):
        headers["host"] = host_header or upstream_host.split(".", 1)[0]

    request_id = getattr(request.state, "request_id", None)
    if request_id:
        headers["X-Request-Id"] = request_id

    user_id = getattr(request.state, "user_id", None)
    if user_id:
        headers["X-User-Id"] = str(user_id)

    user_role = getattr(request.state, "user_role", None)
    if user_role:
        headers["X-User-Role"] = str(user_role)

    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        headers["X-Tenant-Id"] = str(tenant_id)

    tenant_type = getattr(request.state, "tenant_type", None)
    if tenant_type:
        headers["X-Tenant-Type"] = str(tenant_type)

    if user_permissions:
        headers["X-User-Permissions"] = ",".join(sorted(user_permissions))

    body = await request.body()

    client = await get_http_client()
    is_internal_profile_path = full_path == INTERNAL_PROFILE_PREFIX or full_path.startswith(INTERNAL_PROFILE_PREFIX + "/")
    is_platform_directory_path = is_platform_owner_directory_path(full_path)

    if is_platform_directory_path and not is_platform_owner_role(user_role):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Platform Owner access is required",
                "data": None,
                "error": "Forbidden",
                "request_id": request_id,
            },
        )

    if is_internal_profile_path:
        internal_client_id = full_path[len(INTERNAL_PROFILE_PREFIX):].strip("/").split("/", 1)[0]
        if not internal_client_id or not request.headers.get("Authorization"):
            return JSONResponse(status_code=403, content={"success":False,"message":"Internal client authority required","data":None,"error":"Forbidden","request_id":request_id})
        try:
            visible = await _internal_client_visible(client, get_settings().fiteatsy_service_url, request.headers.get("Authorization") or "", internal_client_id)
        except PracticeTenantResolutionError:
            return JSONResponse(status_code=503, content={"success":False,"message":"Internal client authority unavailable","data":None,"error":"Service unavailable","request_id":request_id})
        if not visible:
            return JSONResponse(status_code=404, content={"success":False,"message":"Resource not found","data":None,"error":"Not found","request_id":request_id})

    if (
        is_practice_operations_path(full_path)
        and not is_platform_marketplace_admin_path(full_path)
        and not is_internal_profile_path
        and not is_platform_directory_path
    ):
        try:
            authority = await resolve_practice_tenant_authority(
                client,
                auth_service_url=get_settings().auth_service_url,
                fiteatsy_service_url=get_settings().fiteatsy_service_url,
                authorization=request.headers.get("Authorization"),
                authenticated_user_id=str(user_id) if user_id else None,
            )
        except PracticeTenantResolutionError as exc:
            logger.warning(
                "practice_tenant_resolution_denied",
                path=full_path,
                user_id=user_id,
                reason=str(exc),
            )
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message": "Active External Practice membership required",
                    "data": None,
                    "error": "Forbidden",
                    "request_id": request_id,
                },
            )
        headers["X-Tenant-Id"] = authority.tenant_id
        headers["X-Tenant-Type"] = authority.tenant_type
        headers["X-User-Role"] = authority.membership_role
        if authority.profession_hint:
            headers["X-Profession-Code"] = authority.profession_hint
        addressed_client_id = practice_client_resource_id(full_path)
        if addressed_client_id:
            try:
                client_visible = await client_belongs_to_authenticated_tenant(
                    client,
                    fiteatsy_service_url=get_settings().fiteatsy_service_url,
                    authorization=request.headers.get("Authorization") or "",
                    client_id=addressed_client_id,
                )
            except PracticeTenantResolutionError:
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "message": "External client authority unavailable",
                        "data": None,
                        "error": "Service unavailable",
                        "request_id": request_id,
                    },
                )
            if not client_visible:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Resource not found",
                        "data": None,
                        "error": "Not found",
                        "request_id": request_id,
                    },
                )

    logger.info(
        "proxy_request",
        method=request.method,
        path=full_path,
        target=target_url,
        user_id=user_id,
    )

    try:
        upstream_response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
    except httpx.ConnectError:
        logger.error("upstream_connect_error", target=target_url)
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "message": "Upstream service unavailable",
                "data": None,
                "error": "Bad gateway",
                "request_id": request_id,
            },
        )
    except httpx.TimeoutException:
        logger.error("upstream_timeout", target=target_url)
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "message": "Upstream service timeout",
                "data": None,
                "error": "Gateway timeout",
                "request_id": request_id,
            },
        )

    response_headers = dict(upstream_response.headers)
    response_headers.pop("transfer-encoding", None)
    response_headers.pop("content-encoding", None)

    if request_id:
        response_headers["X-Request-Id"] = request_id

    return StreamingResponse(
        content=upstream_response.iter_bytes(),
        status_code=upstream_response.status_code,
        headers=response_headers,
    )
