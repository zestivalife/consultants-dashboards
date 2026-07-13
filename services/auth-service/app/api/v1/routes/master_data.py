import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.master_data import (
    MasterDataCategoryCreate,
    MasterDataCategoryUpdate,
    MasterDataImportRequest,
    MasterDataItemCreate,
    MasterDataItemUpdate,
)
from app.services import master_data_service

router = APIRouter(tags=["master-data"])


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


@router.get("/categories")
async def list_categories(
    request: Request,
    search: str | None = None,
    scope: str | None = None,
    status: str | None = None,
    include_deleted: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    master_data_service.ensure_master_data_access(current_user, {"master_data.read"})
    result = await master_data_service.list_categories(session, search=search, scope=scope, status=status, include_deleted=include_deleted, page=page, page_size=page_size)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/categories")
async def create_category(body: MasterDataCategoryCreate, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.create"})
    result = await master_data_service.create_category(session, body, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data category created", status_code=201)


@router.patch("/categories/{category_id}")
async def update_category(category_id: uuid.UUID, body: MasterDataCategoryUpdate, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.edit"})
    result = await master_data_service.update_category(session, category_id, body, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data category updated")


@router.delete("/categories/{category_id}")
async def delete_category(category_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.delete"})
    await master_data_service.delete_category(session, category_id, actor=current_user, **_request_meta(request))
    return success_response(message="Master data category deleted")


@router.post("/categories/{category_id}/restore")
async def restore_category(category_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.restore"})
    result = await master_data_service.restore_category(session, category_id, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data category restored")


@router.get("/items")
async def list_items(
    request: Request,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    category_key: str | None = None,
    product_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    status: str | None = None,
    include_deleted: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    master_data_service.ensure_master_data_access(current_user, {"master_data.read"})
    result = await master_data_service.list_items(session, search=search, category_id=category_id, category_key=category_key, product_id=product_id, organization_id=organization_id, status=status, include_deleted=include_deleted, page=page, page_size=page_size)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/items")
async def create_item(body: MasterDataItemCreate, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.create"})
    result = await master_data_service.create_item(session, body, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data item created", status_code=201)


@router.patch("/items/{item_id}")
async def update_item(item_id: uuid.UUID, body: MasterDataItemUpdate, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.edit"})
    result = await master_data_service.update_item(session, item_id, body, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data item updated")


@router.delete("/items/{item_id}")
async def delete_item(item_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.delete"})
    await master_data_service.delete_item(session, item_id, actor=current_user, **_request_meta(request))
    return success_response(message="Master data item deleted")


@router.post("/items/{item_id}/restore")
async def restore_item(item_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.restore"})
    result = await master_data_service.restore_item(session, item_id, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data item restored")


@router.post("/items/import")
async def import_items(body: MasterDataImportRequest, request: Request, session: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    master_data_service.ensure_master_data_access(current_user, {"master_data.import"})
    result = await master_data_service.import_items(session, body, actor=current_user, **_request_meta(request))
    return success_response(data=result.model_dump(mode="json"), message="Master data import completed")


@router.get("/items/export")
async def export_items(
    request: Request,
    category_id: uuid.UUID | None = None,
    category_key: str | None = None,
    status: str | None = None,
    include_deleted: bool = True,
    session: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    master_data_service.ensure_master_data_access(current_user, {"master_data.export"})
    csv_body = await master_data_service.export_items_csv(
        session,
        category_id=category_id,
        category_key=category_key,
        status=status,
        include_deleted=include_deleted,
    )
    return PlainTextResponse(csv_body, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=master-data.csv"})
