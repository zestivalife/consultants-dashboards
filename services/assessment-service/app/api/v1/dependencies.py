import uuid

from fastapi import Request

from app.core.exceptions import UnauthorizedException


def get_user_id(request: Request) -> uuid.UUID:
    user_id_header = request.headers.get("X-User-Id")
    if not user_id_header:
        raise UnauthorizedException("Missing authentication")
    try:
        return uuid.UUID(user_id_header)
    except ValueError:
        raise UnauthorizedException("Invalid user identity")
