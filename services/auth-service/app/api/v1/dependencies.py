import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.services import auth_service


def _extract_identity(request: Request) -> tuple[uuid.UUID, dict]:
    user_id_header = request.headers.get("X-User-Id")
    if user_id_header:
        try:
            return uuid.UUID(user_id_header), {}
        except ValueError as exc:
            raise UnauthorizedException("Invalid user identity") from exc

    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
            subject = payload.get("sub")
            return uuid.UUID(str(subject)), payload
        except Exception as exc:
            raise UnauthorizedException("Invalid or expired access token") from exc

    raise UnauthorizedException("Missing authentication")


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    user_id, payload = _extract_identity(request)
    user = await auth_service.get_current_user(session, user_id)
    user.mfa_assured = bool(payload.get("mfa_assured"))
    return user
