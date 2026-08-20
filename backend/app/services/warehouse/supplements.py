"""True upsert for warehouse business supplements with history."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppException, ErrorCode, ValidationError
from app.models.user import User
from app.models.warehouse import (
    DocumentStatus,
    WarehouseBusinessSupplement,
    WarehouseBusinessSupplementHistory,
)
from app.services.audit_service import AuditAction, ResourceType, create_audit_log
from app.services.warehouse.periods import WarehousePeriodService
from app.services.warehouse.posting import WarehousePostingService, quantize_qty
from app.services.warehouse.scope import WarehouseScopeService

MONEY = Decimal("0.01")
ZERO = Decimal("0")


def _quantize_money(value: Decimal | int | str | None) -> Decimal | None:
    if value is None:
        return None
    quantized = Decimal(value).quantize(MONEY)
    if quantized < ZERO:
        raise ValidationError(message="金额不能为负数")
    return quantized


def _quantize_non_negative(
    value: Decimal | int | str | None, *, field: str
) -> Decimal | None:
    if value is None:
        return None
    quantized = quantize_qty(value)
    if quantized < ZERO:
        raise ValidationError(message=f"{field}不能为负数")
    return quantized


def _snapshot(row: WarehouseBusinessSupplement) -> dict[str, Any]:
    return {
        "document_line_id": row.document_line_id,
        "delivery_note_no": row.delivery_note_no,
        "acceptance_no": row.acceptance_no,
        "contract_no": row.contract_no,
        "manufacturer": row.manufacturer,
        "price_type": row.price_type,
        "unit_price": str(row.unit_price) if row.unit_price is not None else None,
        "amount": str(row.amount) if row.amount is not None else None,
        "weigh_in": str(row.weigh_in) if row.weigh_in is not None else None,
        "residual_value": str(row.residual_value)
        if row.residual_value is not None
        else None,
        "admin_notes": row.admin_notes,
        "version": row.version,
    }


class WarehouseSupplementService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.scope = WarehouseScopeService(db, user)
        self.posting = WarehousePostingService(db, user)
        self.periods = WarehousePeriodService(db, user)

    async def upsert(
        self, document_id: int, payload: dict[str, Any]
    ) -> WarehouseBusinessSupplement:
        document = await self.posting.get_document(document_id, for_update=True)
        warehouse_ids = {
            warehouse_id
            for line in document.lines
            for warehouse_id in (line.source_warehouse_id, line.target_warehouse_id)
            if warehouse_id
        }
        await self.scope.assert_warehouses_access(warehouse_ids, action="补录")
        if document.status == DocumentStatus.VOIDED.value:
            raise AppException(
                error_code=ErrorCode.SUPPLEMENT_FORBIDDEN,
                message="已冲销单据禁止补录修改",
                status_code=409,
            )
        await self.periods.assert_document_period_editable(document.occurred_on)

        document_line_id = payload.get("document_line_id")
        if document_line_id is not None and all(
            line.id != document_line_id for line in document.lines
        ):
            raise ValidationError(message="补录明细不属于当前单据")
        line_key = int(document_line_id or 0)
        values = self._normalized_values(payload)

        existing = await self.db.execute(
            select(WarehouseBusinessSupplement)
            .where(
                WarehouseBusinessSupplement.document_id == document_id,
                WarehouseBusinessSupplement.line_key == line_key,
            )
            .with_for_update()
        )
        row = existing.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if row is None:
            row = WarehouseBusinessSupplement(
                document_id=document_id,
                document_line_id=document_line_id,
                line_key=line_key,
                version=1,
                updated_by=self.user.id,
                created_at=now,
                updated_at=now,
                **values,
            )
            self.db.add(row)
            await self.db.flush()
            await self._write_history(row, version=1)
            await create_audit_log(
                self.db,
                self.user,
                AuditAction.CREATE,
                ResourceType.WAREHOUSE_SUPPLEMENT,
                resource_id=row.id,
                resource_name=document.document_no,
                new_values=_snapshot(row),
            )
            return row

        old_values = _snapshot(row)
        for key, value in values.items():
            setattr(row, key, value)
        row.document_line_id = document_line_id
        row.updated_by = self.user.id
        row.updated_at = now
        row.version = int(row.version or 1) + 1
        await self.db.flush()
        await self._write_history(row, version=row.version)
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE,
            ResourceType.WAREHOUSE_SUPPLEMENT,
            resource_id=row.id,
            resource_name=document.document_no,
            old_values=old_values,
            new_values=_snapshot(row),
        )
        return row

    async def _write_history(
        self, row: WarehouseBusinessSupplement, *, version: int
    ) -> None:
        self.db.add(
            WarehouseBusinessSupplementHistory(
                supplement_id=row.id,
                document_id=row.document_id,
                document_line_id=row.document_line_id,
                version=version,
                payload=json.dumps(_snapshot(row), ensure_ascii=False),
                changed_by=self.user.id,
            )
        )
        await self.db.flush()

    @staticmethod
    def _normalized_values(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "delivery_note_no": payload.get("delivery_note_no"),
            "acceptance_no": payload.get("acceptance_no"),
            "contract_no": payload.get("contract_no"),
            "manufacturer": payload.get("manufacturer"),
            "price_type": payload.get("price_type"),
            "unit_price": _quantize_non_negative(
                payload.get("unit_price"), field="单价"
            ),
            "amount": _quantize_money(payload.get("amount")),
            "weigh_in": _quantize_non_negative(payload.get("weigh_in"), field="过磅重量"),
            "residual_value": _quantize_money(payload.get("residual_value")),
            "admin_notes": payload.get("admin_notes"),
        }


def serialize_supplement(row: WarehouseBusinessSupplement) -> dict[str, Any]:
    return {
        "id": row.id,
        "document_id": row.document_id,
        "document_line_id": row.document_line_id,
        "version": row.version,
        "delivery_note_no": row.delivery_note_no,
        "acceptance_no": row.acceptance_no,
        "contract_no": row.contract_no,
        "manufacturer": row.manufacturer,
        "price_type": row.price_type,
        "unit_price": row.unit_price,
        "amount": row.amount,
        "weigh_in": row.weigh_in,
        "residual_value": row.residual_value,
        "admin_notes": row.admin_notes,
        "updated_by": row.updated_by,
        "updated_at": row.updated_at,
    }
