import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.people_access import (
    BulkActionRequest,
    ManagedUserCreateRequest,
    ManagedUserUpdateRequest,
    OrganizationCreateRequest,
    UserNoteCreateRequest,
)
from app.services import people_access_service


router = APIRouter(tags=["people-access"])


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


@router.get("/summary")
async def get_summary(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.get_summary(session)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/metadata")
async def get_metadata(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.get_metadata(session)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/users")
async def list_users(
    request: Request,
    search: str | None = None,
    role: str | None = None,
    organization_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    status: str | None = None,
    verification: str | None = Query(default=None, pattern="^(verified|pending)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.list_users(
        session,
        search=search,
        role=role,
        organization_id=organization_id,
        department_id=department_id,
        status=status,
        verification=verification,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.get_user_detail(session, user_id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/users")
async def create_user(
    body: ManagedUserCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.create_user(
        session,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="User created", status_code=201)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: ManagedUserUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.update_user(
        session,
        user_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="User updated")


@router.post("/users/{user_id}/notes")
async def add_note(
    user_id: uuid.UUID,
    body: UserNoteCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.add_note(
        session,
        user_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
        message="Note added",
    )


@router.post("/users/bulk-actions")
async def bulk_actions(
    body: BulkActionRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.bulk_action(
        session,
        action=body.action,
        user_ids=body.user_ids,
        actor=current_user,
        organization_id=body.organization_id,
        department_id=body.department_id,
        role_name=body.role,
        package_name=body.package_name,
        status=body.status,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Bulk action applied")


@router.post("/organizations")
async def create_organization(
    body: OrganizationCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await people_access_service.ensure_owner_access(session, current_user)
    result = await people_access_service.create_organization(
        session,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Organization created", status_code=201)
