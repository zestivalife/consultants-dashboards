from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.db.session import get_db
from app.schemas.people_access import CredentialCreateRequest
from app.services import people_access_service

router = APIRouter(tags=["identity"])


def _request_meta(request: Request) -> dict[str, str | None]:
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else None
    if ip_address is None and request.client:
        ip_address = request.client.host
    return {
        "ip_address": ip_address,
        "user_agent": request.headers.get("User-Agent"),
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/password/create")
async def create_credentials(
    body: CredentialCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    result = await people_access_service.create_credentials(
        session,
        body,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Credentials created")
