import jwt as pyjwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

PUBLIC_PATHS: set[str] = {
    "/health",
    "/ready",
    "/version",
    "/api/v1/health",
    "/api/v1/version",
    "/api/v1/versions",
    "/docs",
    "/openapi.json",
    "/redoc",
}

PUBLIC_PREFIXES: list[str] = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/resend-otp",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/forgot-password",
    "/api/v1/onboarding/invitations/validate",
    "/api/v1/onboarding/invitations/accept",
    "/api/v1/onboarding/password/setup",
]

DELEGATED_AUTH_PREFIXES: list[str] = [
    # These routes are owned by auth-service, which validates the access token
    # with the same signing settings that issued it. The gateway should not
    # reject them first with a potentially different deployment secret.
    "/api/v1/auth",
    "/api/v1/owner/people-access",
    "/api/v1/owner/master-data",
    "/api/v1/corporate-admin",
    "/api/v1/team-lead",
    "/api/v1/team-member",
    "/api/v1/notifications",
]


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _is_delegated_auth(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in DELEGATED_AUTH_PREFIXES)


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.headers.get("X-Access-Token")


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if _is_public(request.url.path):
            return await call_next(request)

        if _is_delegated_auth(request.url.path):
            return await call_next(request)

        token = _extract_token(request)
        if not token:
            logger.error(f"Missing token. Path: {request.url.path}, Headers: {dict(request.headers)}")
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Missing authentication token",
                    "data": None,
                    "error": "Missing authentication token",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        settings = get_settings()
        try:
            payload = pyjwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except pyjwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Token has expired",
                    "data": None,
                    "error": "Token has expired",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
        except pyjwt.InvalidTokenError as exc:
            logger.warning("jwt_invalid", error=str(exc))
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Invalid token",
                    "data": None,
                    "error": "Invalid token",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        request.state.user_id = payload.get("sub")
        request.state.user_role = payload.get("role", "member")
        request.state.user_permissions = payload.get("permissions", []) or []
        request.state.token_payload = payload

        return await call_next(request)
