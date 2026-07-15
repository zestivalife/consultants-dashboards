import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.people_access import (
    BulkActionRequest,
    CsvImportRequest,
    CustomRoleCreateRequest,
    InvitationCreateRequest,
    ManagedUserCreateRequest,
    ManagedUserUpdateRequest,
    OrganizationCreateRequest,
    RoleCloneRequest,
    RolePermissionUpdateRequest,
    UserAttachmentCreateRequest,
    UserPackageAssignmentRequest,
    UserProductAssignmentRequest,
    UserServiceAssignmentRequest,
    UserNoteCreateRequest,
)
from app.services import people_access_service


router = APIRouter(tags=["people-access"])


async def _require_people_access(
    session: AsyncSession,
    current_user: UserResponse,
    *permissions: str,
) -> None:
    await people_access_service.ensure_owner_access(
        session,
        current_user,
        set(permissions),
    )


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
    await _require_people_access(session, current_user, "users.read")
    result = await people_access_service.get_summary(session)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/metadata")
async def get_metadata(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.read")
    result = await people_access_service.get_metadata(session)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/users")
async def list_users(
    request: Request,
    search: str | None = None,
    role: str | None = None,
    organization_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    status: str | None = None,
    verification: str | None = Query(default=None, pattern="^(verified|pending)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.read")
    result = await people_access_service.list_users(
        session,
        search=search,
        role=role,
        organization_id=organization_id,
        department_id=department_id,
        product_id=product_id,
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
    await _require_people_access(session, current_user, "users.read")
    result = await people_access_service.get_user_detail(session, user_id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/users")
async def create_user(
    body: ManagedUserCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.create")
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
    await _require_people_access(session, current_user, "users.edit")
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
    await _require_people_access(session, current_user, "users.edit")
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


@router.post("/users/{user_id}/attachments")
async def add_attachment(
    user_id: uuid.UUID,
    body: UserAttachmentCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.edit")
    result = await people_access_service.add_attachment(
        session,
        user_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=[item.model_dump(mode="json") for item in result], message="Attachment added")


@router.get("/invitations")
async def list_invitations(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.read")
    items, pagination = await people_access_service.list_invitations(
        session,
        search=search,
        status=status,
        page=page,
        page_size=page_size,
    )
    return success_response(
        data={
            "items": [item.model_dump(mode="json") for item in items],
            "pagination": pagination.model_dump(mode="json"),
        }
    )


@router.post("/invitations")
async def create_invitation(
    body: InvitationCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.invite")
    result = await people_access_service.create_invitation(
        session,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Invitation created", status_code=201)


@router.post("/invitations/{invitation_id}/resend")
async def resend_invitation(
    invitation_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.invite")
    result = await people_access_service.resend_invitation(
        session,
        invitation_id,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Invitation resent")


@router.post("/invitations/{invitation_id}/cancel")
async def cancel_invitation(
    invitation_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.invite")
    result = await people_access_service.cancel_invitation(
        session,
        invitation_id,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Invitation cancelled")


@router.post("/invitations/{invitation_id}/expire")
async def expire_invitation(
    invitation_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.invite")
    result = await people_access_service.expire_invitation(
        session,
        invitation_id,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Invitation expired")


@router.patch("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: uuid.UUID,
    body: RolePermissionUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "settings.manage")
    result = await people_access_service.update_role_permissions(
        session,
        role_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Role permissions updated")


@router.post("/roles")
async def create_custom_role(
    body: CustomRoleCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "settings.manage")
    result = await people_access_service.create_custom_role(
        session,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Role created", status_code=201)


@router.post("/roles/{role_id}/clone")
async def clone_role(
    role_id: uuid.UUID,
    body: RoleCloneRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "settings.manage")
    result = await people_access_service.clone_role(
        session,
        role_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Role cloned", status_code=201)


@router.put("/users/{user_id}/products")
async def assign_products(
    user_id: uuid.UUID,
    body: list[UserProductAssignmentRequest],
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.edit")
    result = await people_access_service.assign_products(
        session,
        user_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=[item.model_dump(mode="json") for item in result], message="Products assigned")


@router.put("/users/{user_id}/packages")
async def assign_packages(
    user_id: uuid.UUID,
    body: list[UserPackageAssignmentRequest],
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "packages.manage")
    result = await people_access_service.assign_packages(
        session,
        user_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=[item.model_dump(mode="json") for item in result], message="Packages assigned")


@router.put("/users/{user_id}/services")
async def assign_services(
    user_id: uuid.UUID,
    body: list[UserServiceAssignmentRequest],
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "services.manage")
    result = await people_access_service.assign_services(
        session,
        user_id,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=[item.model_dump(mode="json") for item in result], message="Services assigned")


@router.post("/users/{user_id}/sessions/{session_id}/revoke")
async def revoke_user_session(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.force_logout")
    result = await people_access_service.revoke_user_session(
        session,
        user_id,
        session_id,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=[item.model_dump(mode="json") for item in result], message="Session revoked")


@router.post("/users/{user_id}/force-logout")
async def force_logout_user(
    user_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.force_logout")
    result = await people_access_service.force_logout_user(
        session,
        user_id,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=[item.model_dump(mode="json") for item in result], message="User logged out from all devices")


@router.get("/exports/users")
async def export_users(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.export")
    csv_content = await people_access_service.export_users_csv(session)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="people-access-export.csv"'},
    )


@router.post("/users/import")
async def import_users(
    body: CsvImportRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.import")
    result = await people_access_service.import_users(
        session,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Import completed")


@router.post("/users/bulk-actions")
async def bulk_actions(
    body: BulkActionRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await _require_people_access(session, current_user, "users.edit", "users.invite")
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
    await _require_people_access(session, current_user, "organizations.manage")
    result = await people_access_service.create_organization(
        session,
        body,
        actor=current_user,
        **_request_meta(request),
    )
    return success_response(data=result.model_dump(mode="json"), message="Organization created", status_code=201)
