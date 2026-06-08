import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.services import auth_service


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        raise UnauthorizedException("Missing authentication")

    try:
        user_id = uuid.UUID(user_id_header)
    except ValueError:
        raise UnauthorizedException("Invalid user identity")

    return await auth_service.get_current_user(session, user_id)
