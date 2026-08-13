"""Warehouse count (stocktake) service."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException, ErrorCode, ResourceNotFoundError, ValidationError
from app.models.user import User
from sqlalchemy.dialects.postgresql import insert

from app.models.warehouse import (
    CountStatus,
    WarehouseCount,
    WarehouseCountLine,
    WarehouseDocumentCounter,
    WarehouseStockBalance,
)
from app.services.audit_service import AuditAction, ResourceType, create_audit_log
from app.services.warehouse.codes import format_sequence
from app.services.warehouse.posting import WarehousePostingService, quantize_qty
from app.services.warehouse.scope import WarehouseScopeService


class WarehouseCountService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.scope = WarehouseScopeService(db, user)
        self.posting = WarehousePostingService(db, user)

    async def create_count(
        self,
        *,
        warehouse_id: int,
        counted_on: date,
        location_id: Optional[int] = None,
        project_id: Optional[int] = None,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> WarehouseCount:
        if idempotency_key:
            existing = await self.db.execute(
                select(WarehouseCount)
                .options(selectinload(WarehouseCount.lines))
                .where(
                    WarehouseCount.created_by == self.user.id,
                    WarehouseCount.idempotency_key == idempotency_key,
                )
            )
            existing_count = existing.scalar_one_or_none()
            if existing_count is not None:
                return await self.get_count(existing_count.id)
        await self.scope.assert_warehouse_access(warehouse_id, for_posting=True, action="盘点")
        count_no = await self._next_count_no(counted_on)
        count = WarehouseCount(
            count_no=count_no,
            warehouse_id=warehouse_id,
            location_id=location_id,
            project_id=project_id,
            counted_on=counted_on,
            status=CountStatus.DRAFT.value,
            description=description,
            idempotency_key=idempotency_key,
            created_by=self.user.id,
        )
        self.db.add(count)
        await self.db.flush()

        query = select(WarehouseStockBalance).where(
            WarehouseStockBalance.warehouse_id == warehouse_id
        )
        if location_id:
            query = query.where(WarehouseStockBalance.location_id == location_id)
        if project_id:
            query = query.where(WarehouseStockBalance.project_id == project_id)
        result = await self.db.execute(query)
        for balance in result.scalars().all():
            self.db.add(
                WarehouseCountLine(
                    count_id=count.id,
                    warehouse_id=balance.warehouse_id,
                    location_id=balance.location_id,
                    project_id=balance.project_id,
                    material_id=balance.material_id,
                    book_quantity=quantize_qty(balance.quantity),
                    counted_quantity=None,
                )
            )
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.CREATE,
            ResourceType.WAREHOUSE_COUNT,
            resource_id=count.id,
            resource_name=count.count_no,
            new_values={"warehouse_id": warehouse_id, "counted_on": str(counted_on)},
        )
        return await self.get_count(count.id)

    async def update_lines(self, count_id: int, lines: Sequence[dict]) -> WarehouseCount:
        count = await self.get_count(count_id, for_update=True)
        await self.scope.assert_warehouse_access(
            count.warehouse_id, for_posting=True, action="盘点录入"
        )
        if count.status not in {CountStatus.DRAFT.value, CountStatus.ENTERED.value}:
            raise ValidationError(message="已确认的盘点不能再改实盘数量")
        line_map = {line.id: line for line in count.lines}
        for payload in lines:
            line = line_map.get(payload["id"])
            if line is None:
                raise ValidationError(message=f"盘点明细不存在: {payload['id']}")
            line.counted_quantity = quantize_qty(payload["counted_quantity"])
        count.status = CountStatus.ENTERED.value
        await self.db.flush()
        return await self.get_count(count.id)

    async def confirm(self, count_id: int) -> WarehouseCount:
        count = await self.get_count(count_id, for_update=True)
        await self.scope.assert_warehouse_access(
            count.warehouse_id, for_posting=True, action="盘点确认"
        )
        if count.status == CountStatus.CONFIRMED.value:
            raise AppException(
                error_code=ErrorCode.WAREHOUSE_CONFLICT,
                message="盘点已确认，不能重复过账",
                status_code=409,
            )
        if count.status == CountStatus.VOIDED.value:
            raise ValidationError(message="已作废的盘点不能确认")

        adjustment_lines = []
        for line in count.lines:
            if line.counted_quantity is None:
                raise ValidationError(message="存在未录入实盘数量的明细")
            delta = quantize_qty(line.counted_quantity) - quantize_qty(line.book_quantity)
            if delta == Decimal("0"):
                continue
            adjustment_lines.append(
                {
                    "material_id": line.material_id,
                    "quantity": delta,
                    "warehouse_id": line.warehouse_id,
                    "location_id": line.location_id,
                    "project_id": line.project_id,
                }
            )

        adjustment = None
        if adjustment_lines:
            adjustment = await self.posting.post_count_adjustment(
                occurred_on=count.counted_on,
                handler=self.user.full_name or self.user.username,
                reference_no=count.count_no,
                lines=adjustment_lines,
                description=f"盘点调整 {count.count_no}",
                idempotency_key=f"count-adjust-{count.id}",
                ignore_count_id=count.id,
            )
            for line in count.lines:
                counted = quantize_qty(line.counted_quantity or 0)
                if counted != quantize_qty(line.book_quantity):
                    line.adjustment_document_id = adjustment.id

        now = datetime.now(timezone.utc)
        count.status = CountStatus.CONFIRMED.value
        count.confirmed_by = self.user.id
        count.confirmed_at = now
        count.adjustment_document_id = adjustment.id if adjustment else None
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE,
            ResourceType.WAREHOUSE_COUNT,
            resource_id=count.id,
            resource_name=count.count_no,
            description=f"确认盘点 {count.count_no}",
            new_values={"adjustment_document_id": count.adjustment_document_id},
        )
        return await self.get_count(count.id)

    async def get_count(self, count_id: int, *, for_update: bool = False) -> WarehouseCount:
        statement = (
            select(WarehouseCount)
            .options(
                selectinload(WarehouseCount.warehouse),
                selectinload(WarehouseCount.location),
                selectinload(WarehouseCount.project),
                selectinload(WarehouseCount.lines).selectinload(WarehouseCountLine.material),
                selectinload(WarehouseCount.lines).selectinload(WarehouseCountLine.location),
                selectinload(WarehouseCount.lines).selectinload(WarehouseCountLine.project),
            )
            .where(WarehouseCount.id == count_id)
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self.db.execute(statement)
        count = result.scalar_one_or_none()
        if count is None:
            raise ResourceNotFoundError(resource_type="盘点", resource_id=count_id)
        return count

    async def list_counts(self) -> list[WarehouseCount]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=False)
        query = (
            select(WarehouseCount)
            .options(selectinload(WarehouseCount.warehouse))
            .order_by(WarehouseCount.counted_on.desc(), WarehouseCount.id.desc())
        )
        if allowed is not None:
            query = query.where(WarehouseCount.warehouse_id.in_(allowed or [-1]))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _next_count_no(self, counted_on: date) -> str:
        prefix = "PD"
        await self.db.execute(
            insert(WarehouseDocumentCounter)
            .values(prefix=prefix, occurred_on=counted_on, next_number=1)
            .on_conflict_do_nothing(index_elements=["prefix", "occurred_on"])
        )
        await self.db.flush()
        result = await self.db.execute(
            select(WarehouseDocumentCounter)
            .where(
                WarehouseDocumentCounter.prefix == prefix,
                WarehouseDocumentCounter.occurred_on == counted_on,
            )
            .with_for_update()
        )
        counter = result.scalar_one()
        number = int(counter.next_number)
        counter.next_number = number + 1
        await self.db.flush()
        return f"{prefix}-{counted_on.strftime('%Y%m%d')}-{format_sequence(number, 4)}"
