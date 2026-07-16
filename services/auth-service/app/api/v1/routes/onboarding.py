from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.db.session import get_db
from app.schemas.people_access import InvitationTokenRequest
from app.services import people_access_service


router = APIRouter(tags=["onboarding"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _request_meta(request: Request) -> dict[str, str | None]:
    return {
        "ip_address": _client_ip(request),
        "user_agent": request.headers.get("User-Agent"),
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/invitations/validate")
async def validate_invitation(
    body: InvitationTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    result = await people_access_service.validate_invitation_token(
        session,
        body.token,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Invitation is valid")


@router.post("/invitations/accept")
async def accept_invitation(
    body: InvitationTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    result = await people_access_service.accept_invitation(
        session,
        body.token,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Invitation accepted")


@router.post("/password/setup")
async def initiate_password_setup(
    body: InvitationTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    result = await people_access_service.initiate_password_setup(
        session,
        body.token,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Password setup initiated")
