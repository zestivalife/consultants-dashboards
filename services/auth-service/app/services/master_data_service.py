import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.db.models.master_data import MasterDataCategory, MasterDataItem
from app.repositories.master_data_repository import MasterDataRepository
from app.schemas.auth import UserResponse
from app.schemas.master_data import (
    MasterDataCategoryCreate,
    MasterDataCategoryListResponse,
    MasterDataCategoryResponse,
    MasterDataCategoryUpdate,
    MasterDataImportRequest,
    MasterDataImportResponse,
    MasterDataItemCreate,
    MasterDataItemListResponse,
    MasterDataItemResponse,
    MasterDataItemUpdate,
    PaginationMeta,
)


def ensure_master_data_access(current_user: UserResponse, required: set[str]) -> None:
    if set(current_user.permissions or []) & required:
        return
    raise ForbiddenException("You do not have permission to manage master data")


def _total_pages(total: int, page_size: int) -> int:
    return max(1, (total + page_size - 1) // page_size)


def _category_response(category: MasterDataCategory, counts: tuple[int, int] = (0, 0)) -> MasterDataCategoryResponse:
    item_count, active_item_count = counts
    return MasterDataCategoryResponse(
        id=category.id,
        scope=category.scope,
        key=category.key,
        name=category.name,
        description=category.description,
        status=category.status,
        is_system=category.is_system,
        sort_order=category.sort_order,
        metadata_schema=category.metadata_schema or {},
        item_count=item_count,
        active_item_count=active_item_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
        deleted_at=category.deleted_at,
    )


def _item_response(item: MasterDataItem) -> MasterDataItemResponse:
    return MasterDataItemResponse(
        id=item.id,
        category_id=item.category_id,
        category_key=item.category.key if item.category else "",
        category_name=item.category.name if item.category else "",
        product_id=item.product_id,
        product=item.product.name if item.product else None,
        organization_id=item.organization_id,
        organization=item.organization.name if item.organization else None,
        code=item.code,
        label=item.label,
        description=item.description,
        status=item.status,
        sort_order=item.sort_order,
        metadata=item.meta or {},
        effective_from=item.effective_from,
        effective_to=item.effective_to,
        created_at=item.created_at,
        updated_at=item.updated_at,
        deleted_at=item.deleted_at,
    )


async def _audit(
    repo: MasterDataRepository,
    *,
    actor: UserResponse,
    entity_type: str,
    entity_id: str,
    action: str,
    before_state: dict | None,
    after_state: dict | None,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> None:
    await repo.add_audit_event(
        actor_user_id=actor.id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


async def list_categories(
    session: AsyncSession,
    *,
    search: str | None,
    scope: str | None,
    status: str | None,
    include_deleted: bool,
    page: int,
    page_size: int,
) -> MasterDataCategoryListResponse:
    repo = MasterDataRepository(session)
    categories, total = await repo.list_categories(
        search=search,
        scope=scope.upper() if scope else None,
        status=status.upper() if status else None,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size,
    )
    counts = await repo.category_counts([category.id for category in categories])
    return MasterDataCategoryListResponse(
        items=[_category_response(category, counts.get(category.id, (0, 0))) for category in categories],
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=_total_pages(total, page_size)),
    )


async def create_category(session: AsyncSession, payload: MasterDataCategoryCreate, *, actor: UserResponse, **meta) -> MasterDataCategoryResponse:
    repo = MasterDataRepository(session)
    category = MasterDataCategory(**payload.model_dump(), created_by_user_id=actor.id, updated_by_user_id=actor.id)
    try:
        await repo.create_category(category)
        after = _category_response(category).model_dump(mode="json")
        await _audit(repo, actor=actor, entity_type="master_data_category", entity_id=str(category.id), action="master_data.category.create", before_state=None, after_state=after, **meta)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictException("A master data category with this scope and key already exists") from exc
    return _category_response(category)


async def update_category(session: AsyncSession, category_id: uuid.UUID, payload: MasterDataCategoryUpdate, *, actor: UserResponse, **meta) -> MasterDataCategoryResponse:
    repo = MasterDataRepository(session)
    category = await repo.get_category(category_id)
    if not category:
        raise NotFoundException("Master data category not found")
    before = _category_response(category).model_dump(mode="json")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    category.updated_by_user_id = actor.id
    try:
        await session.flush()
        after = _category_response(category).model_dump(mode="json")
        await _audit(repo, actor=actor, entity_type="master_data_category", entity_id=str(category.id), action="master_data.category.update", before_state=before, after_state=after, **meta)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictException("A master data category with this scope and key already exists") from exc
    return _category_response(category)


async def delete_category(session: AsyncSession, category_id: uuid.UUID, *, actor: UserResponse, **meta) -> None:
    repo = MasterDataRepository(session)
    category = await repo.get_category(category_id)
    if not category:
        raise NotFoundException("Master data category not found")
    before = _category_response(category).model_dump(mode="json")
    category.status = "DELETED"
    category.deleted_at = datetime.now(timezone.utc)
    category.updated_by_user_id = actor.id
    after = _category_response(category).model_dump(mode="json")
    await _audit(repo, actor=actor, entity_type="master_data_category", entity_id=str(category.id), action="master_data.category.delete", before_state=before, after_state=after, **meta)
    await session.commit()


async def restore_category(session: AsyncSession, category_id: uuid.UUID, *, actor: UserResponse, **meta) -> MasterDataCategoryResponse:
    repo = MasterDataRepository(session)
    category = await repo.get_category(category_id)
    if not category:
        raise NotFoundException("Master data category not found")
    before = _category_response(category).model_dump(mode="json")
    category.status = "ACTIVE"
    category.deleted_at = None
    category.updated_by_user_id = actor.id
    after = _category_response(category).model_dump(mode="json")
    await _audit(repo, actor=actor, entity_type="master_data_category", entity_id=str(category.id), action="master_data.category.restore", before_state=before, after_state=after, **meta)
    await session.commit()
    return _category_response(category)


async def list_items(session: AsyncSession, **kwargs) -> MasterDataItemListResponse:
    repo = MasterDataRepository(session)
    if kwargs.get("status"):
        kwargs["status"] = kwargs["status"].upper()
    items, total = await repo.list_items(**kwargs)
    return MasterDataItemListResponse(
        items=[_item_response(item) for item in items],
        pagination=PaginationMeta(
            page=kwargs["page"],
            page_size=kwargs["page_size"],
            total=total,
            total_pages=_total_pages(total, kwargs["page_size"]),
        ),
    )


async def create_item(session: AsyncSession, payload: MasterDataItemCreate, *, actor: UserResponse, **meta) -> MasterDataItemResponse:
    repo = MasterDataRepository(session)
    if not await repo.get_category(payload.category_id):
        raise NotFoundException("Master data category not found")
    if payload.product_id and not await repo.get_product(payload.product_id):
        raise NotFoundException("Product not found")
    if payload.organization_id and not await repo.get_organization(payload.organization_id):
        raise NotFoundException("Organization not found")
    data = payload.model_dump()
    data["meta"] = data.pop("metadata", {})
    item = MasterDataItem(**data, created_by_user_id=actor.id, updated_by_user_id=actor.id)
    try:
        await repo.create_item(item)
        await session.flush()
        item = await repo.get_item(item.id) or item
        after = _item_response(item).model_dump(mode="json")
        await _audit(repo, actor=actor, entity_type="master_data_item", entity_id=str(item.id), action="master_data.item.create", before_state=None, after_state=after, **meta)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictException("A master data item with this category and code already exists") from exc
    return _item_response(item)


async def update_item(session: AsyncSession, item_id: uuid.UUID, payload: MasterDataItemUpdate, *, actor: UserResponse, **meta) -> MasterDataItemResponse:
    repo = MasterDataRepository(session)
    item = await repo.get_item(item_id)
    if not item:
        raise NotFoundException("Master data item not found")
    before = _item_response(item).model_dump(mode="json")
    data = payload.model_dump(exclude_unset=True)
    if data.get("category_id") and not await repo.get_category(data["category_id"]):
        raise NotFoundException("Master data category not found")
    if data.get("product_id") and not await repo.get_product(data["product_id"]):
        raise NotFoundException("Product not found")
    if data.get("organization_id") and not await repo.get_organization(data["organization_id"]):
        raise NotFoundException("Organization not found")
    if "metadata" in data:
        data["meta"] = data.pop("metadata") or {}
    for key, value in data.items():
        setattr(item, key, value)
    item.updated_by_user_id = actor.id
    try:
        await session.flush()
        item = await repo.get_item(item.id) or item
        after = _item_response(item).model_dump(mode="json")
        await _audit(repo, actor=actor, entity_type="master_data_item", entity_id=str(item.id), action="master_data.item.update", before_state=before, after_state=after, **meta)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictException("A master data item with this category and code already exists") from exc
    return _item_response(item)


async def delete_item(session: AsyncSession, item_id: uuid.UUID, *, actor: UserResponse, **meta) -> None:
    repo = MasterDataRepository(session)
    item = await repo.get_item(item_id)
    if not item:
        raise NotFoundException("Master data item not found")
    before = _item_response(item).model_dump(mode="json")
    item.status = "DELETED"
    item.deleted_at = datetime.now(timezone.utc)
    item.updated_by_user_id = actor.id
    after = _item_response(item).model_dump(mode="json")
    await _audit(repo, actor=actor, entity_type="master_data_item", entity_id=str(item.id), action="master_data.item.delete", before_state=before, after_state=after, **meta)
    await session.commit()


async def restore_item(session: AsyncSession, item_id: uuid.UUID, *, actor: UserResponse, **meta) -> MasterDataItemResponse:
    repo = MasterDataRepository(session)
    item = await repo.get_item(item_id)
    if not item:
        raise NotFoundException("Master data item not found")
    before = _item_response(item).model_dump(mode="json")
    item.status = "ACTIVE"
    item.deleted_at = None
    item.updated_by_user_id = actor.id
    after = _item_response(item).model_dump(mode="json")
    await _audit(repo, actor=actor, entity_type="master_data_item", entity_id=str(item.id), action="master_data.item.restore", before_state=before, after_state=after, **meta)
    await session.commit()
    return _item_response(item)


async def import_items(session: AsyncSession, payload: MasterDataImportRequest, *, actor: UserResponse, **meta) -> MasterDataImportResponse:
    repo = MasterDataRepository(session)
    created = updated = skipped = 0
    errors: list[str] = []
    for index, row in enumerate(payload.rows, start=1):
        category = await repo.get_category_by_key(row.category_key)
        if not category:
            errors.append(f"Row {index}: category '{row.category_key}' not found")
            skipped += 1
            continue
        existing = await repo.get_item_by_code(category.id, row.code)
        data = row.model_dump(exclude={"category_key"})
        if existing:
            existing_loaded = await repo.get_item(existing.id) or existing
            before = _item_response(existing_loaded).model_dump(mode="json")
            if "metadata" in data:
                data["meta"] = data.pop("metadata") or {}
            for key, value in data.items():
                setattr(existing, key, value)
            existing.category_id = category.id
            existing.updated_by_user_id = actor.id
            updated += 1
            await _audit(repo, actor=actor, entity_type="master_data_item", entity_id=str(existing.id), action="master_data.item.import_update", before_state=before, after_state=data, **meta)
        else:
            data["meta"] = data.pop("metadata", {})
            item = MasterDataItem(category_id=category.id, **data, created_by_user_id=actor.id, updated_by_user_id=actor.id)
            await repo.create_item(item)
            created += 1
            await _audit(repo, actor=actor, entity_type="master_data_item", entity_id=str(item.id), action="master_data.item.import_create", before_state=None, after_state=data, **meta)
    await session.commit()
    return MasterDataImportResponse(created=created, updated=updated, skipped=skipped, errors=errors)


async def export_items_csv(
    session: AsyncSession,
    *,
    category_id: uuid.UUID | None = None,
    category_key: str | None = None,
    status: str | None = None,
    include_deleted: bool = True,
) -> str:
    response = await list_items(
        session,
        search=None,
        category_id=category_id,
        category_key=category_key,
        product_id=None,
        organization_id=None,
        status=status,
        include_deleted=include_deleted,
        page=1,
        page_size=5000,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["category_key", "code", "label", "description", "status", "sort_order"])
    for item in response.items:
        writer.writerow([item.category_key, item.code, item.label, item.description or "", item.status, item.sort_order])
    return buffer.getvalue()
