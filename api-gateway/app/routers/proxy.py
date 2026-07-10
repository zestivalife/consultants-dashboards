import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.config import get_settings

logger = structlog.get_logger(__name__)

router = APIRouter()

_client: httpx.AsyncClient | None = None

OWNER_ACCESS_RULES: tuple[tuple[str, str, set[str]], ...] = (
    ("/api/v1/owner/people-access/summary", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/metadata", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/users/bulk-actions", "POST", {"users.edit", "users.invite"}),
    ("/api/v1/owner/people-access/users", "POST", {"users.create"}),
    ("/api/v1/owner/people-access/users/", "POST", {"users.edit"}),
    ("/api/v1/owner/people-access/users/", "PATCH", {"users.edit"}),
    ("/api/v1/owner/people-access/users/", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/users", "GET", {"users.read"}),
    ("/api/v1/owner/people-access/organizations", "POST", {"organizations.manage"}),
)


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


def _resolve_upstream(path: str) -> tuple[str, str] | None:
    """Match the request path to an upstream service URL. Returns (upstream_base, remaining_path)."""
    settings = get_settings()
    routes = settings.get_service_routes()
    for route in routes:
        prefix = route["prefix"]
        if path == prefix or path.startswith(prefix + "/"):
            remaining = path[len(prefix):]
            logger.debug("route_match_success", path=path, prefix=prefix, upstream=route["upstream"])
            return route["upstream"], remaining
    logger.warning("route_match_failure", path=path)
    return None


def _required_permissions(path: str, method: str) -> set[str]:
    for prefix, allowed_method, permissions in OWNER_ACCESS_RULES:
        if method == allowed_method and path.startswith(prefix):
            return permissions
    return set()


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy(request: Request, path: str):
    full_path = f"/{path}"
    required_permissions = _required_permissions(full_path, request.method.upper())
    user_permissions = set(getattr(request.state, "user_permissions", []) or [])
    if required_permissions and not (user_permissions & required_permissions):
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

    upstream_base, _ = resolved
    target_url = f"{upstream_base}{full_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    headers = dict(request.headers)
    headers.pop("host", None)

    request_id = getattr(request.state, "request_id", None)
    if request_id:
        headers["X-Request-Id"] = request_id

    user_id = getattr(request.state, "user_id", None)
    if user_id:
        headers["X-User-Id"] = str(user_id)

    user_role = getattr(request.state, "user_role", None)
    if user_role:
        headers["X-User-Role"] = str(user_role)

    if user_permissions:
        headers["X-User-Permissions"] = ",".join(sorted(user_permissions))

    body = await request.body()

    client = await get_http_client()

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
