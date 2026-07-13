import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.master_data import MasterDataCategory, MasterDataItem
from app.db.models.owner_access import AuditEvent, Organization, Product


class MasterDataRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_categories(self, *, search: str | None, scope: str | None, status: str | None, include_deleted: bool, page: int, page_size: int) -> tuple[list[MasterDataCategory], int]:
        stmt = select(MasterDataCategory)
        count_stmt = select(func.count(MasterDataCategory.id))
        filters = []
        if search:
            term = f"%{search.lower()}%"
            filters.append(or_(func.lower(MasterDataCategory.key).like(term), func.lower(MasterDataCategory.name).like(term), func.lower(MasterDataCategory.description).like(term)))
        if scope:
            filters.append(MasterDataCategory.scope == scope)
        if status:
            filters.append(MasterDataCategory.status == status)
        if not include_deleted:
            filters.append(MasterDataCategory.deleted_at.is_(None))
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(MasterDataCategory.sort_order.asc(), MasterDataCategory.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def category_counts(self, category_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[int, int]]:
        if not category_ids:
            return {}
        result = await self._session.execute(
            select(
                MasterDataItem.category_id,
                func.count(MasterDataItem.id),
                func.count(MasterDataItem.id).filter(MasterDataItem.deleted_at.is_(None), MasterDataItem.status == "ACTIVE"),
            )
            .where(MasterDataItem.category_id.in_(category_ids))
            .group_by(MasterDataItem.category_id)
        )
        return {row[0]: (row[1], row[2]) for row in result.all()}

    async def get_category(self, category_id: uuid.UUID) -> MasterDataCategory | None:
        return await self._session.get(MasterDataCategory, category_id)

    async def get_category_by_key(self, key: str, scope: str = "GLOBAL") -> MasterDataCategory | None:
        result = await self._session.execute(select(MasterDataCategory).where(MasterDataCategory.key == key, MasterDataCategory.scope == scope))
        return result.scalar_one_or_none()

    async def create_category(self, category: MasterDataCategory) -> MasterDataCategory:
        self._session.add(category)
        await self._session.flush()
        return category

    async def list_items(self, *, search: str | None, category_id: uuid.UUID | None, category_key: str | None, product_id: uuid.UUID | None, organization_id: uuid.UUID | None, status: str | None, include_deleted: bool, page: int, page_size: int) -> tuple[list[MasterDataItem], int]:
        stmt = select(MasterDataItem).options(selectinload(MasterDataItem.category), selectinload(MasterDataItem.product), selectinload(MasterDataItem.organization))
        count_stmt = select(func.count(MasterDataItem.id))
        filters = []
        if category_key:
            stmt = stmt.join(MasterDataCategory)
            count_stmt = count_stmt.join(MasterDataCategory)
            filters.append(MasterDataCategory.key == category_key)
        if search:
            term = f"%{search.lower()}%"
            filters.append(or_(func.lower(MasterDataItem.code).like(term), func.lower(MasterDataItem.label).like(term), func.lower(MasterDataItem.description).like(term)))
        if category_id:
            filters.append(MasterDataItem.category_id == category_id)
        if product_id:
            filters.append(MasterDataItem.product_id == product_id)
        if organization_id:
            filters.append(MasterDataItem.organization_id == organization_id)
        if status:
            filters.append(MasterDataItem.status == status)
        if not include_deleted:
            filters.append(MasterDataItem.deleted_at.is_(None))
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(MasterDataItem.sort_order.asc(), MasterDataItem.label.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_item(self, item_id: uuid.UUID) -> MasterDataItem | None:
        result = await self._session.execute(
            select(MasterDataItem)
            .options(selectinload(MasterDataItem.category), selectinload(MasterDataItem.product), selectinload(MasterDataItem.organization))
            .where(MasterDataItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_item_by_code(self, category_id: uuid.UUID, code: str) -> MasterDataItem | None:
        result = await self._session.execute(select(MasterDataItem).where(MasterDataItem.category_id == category_id, MasterDataItem.code == code))
        return result.scalar_one_or_none()

    async def create_item(self, item: MasterDataItem) -> MasterDataItem:
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_product(self, product_id: uuid.UUID) -> Product | None:
        return await self._session.get(Product, product_id)

    async def get_organization(self, organization_id: uuid.UUID) -> Organization | None:
        return await self._session.get(Organization, organization_id)

    async def add_audit_event(self, *, actor_user_id: uuid.UUID | None, entity_type: str, entity_id: str, action: str, before_state: dict | None, after_state: dict | None, ip_address: str | None, user_agent: str | None, request_id: str | None) -> None:
        self._session.add(
            AuditEvent(
                actor_user_id=actor_user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                before_state=before_state,
                after_state=after_state,
                ip_address=ip_address,
                browser=user_agent,
                request_id=request_id,
                created_at=datetime.now(timezone.utc),
            )
        )
