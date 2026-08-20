"""Immutable inventory posting engine."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException, ErrorCode, ValidationError
from app.core.permissions import Permission, has_permission
from app.models.user import User
from app.models.warehouse import (
    CountStatus,
    DocumentStatus,
    DocumentType,
    ScrapDisposalStatus,
    Warehouse,
    WarehouseBalanceRepair,
    WarehouseCount,
    WarehouseDocument,
    WarehouseDocumentLine,
    WarehouseLedgerEntry,
    WarehouseLocation,
    WarehouseMaterial,
    WarehouseProject,
    WarehouseStockBalance,
)
from app.services.audit_service import AuditAction, ResourceType, create_audit_log
from app.services.warehouse.codes import generate_document_no
from app.services.warehouse.scope import WarehouseScopeService

QTY = Decimal("0.0001")
ZERO = Decimal("0.0000")


def quantize_qty(value: Decimal | int | str, scale: int = 4) -> Decimal:
    scale = max(0, min(int(scale), 4))
    quantum = Decimal(1).scaleb(-scale)
    return Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, order=True)
class StockKey:
    warehouse_id: int
    location_id: int
    project_id: int
    material_id: int
    batch_no: str = ""
    serial_no: str = ""


@dataclass(frozen=True)
class PlannedDelta:
    key: StockKey
    quantity_delta: Decimal
    document_line_id: int


def _insufficient_stock_error(
    key: StockKey, available: Decimal, requested: Decimal
) -> AppException:
    return AppException(
        error_code=ErrorCode.INSUFFICIENT_STOCK,
        message=f"库存不足，当前可用 {quantize_qty(available)}",
        detail="当前维度可用库存不足，请刷新后改库位或联系管理员",
        status_code=409,
        data={
            "warehouse_id": key.warehouse_id,
            "location_id": key.location_id,
            "project_id": key.project_id,
            "material_id": key.material_id,
            "batch_no": key.batch_no,
            "serial_no": key.serial_no,
            "available": str(quantize_qty(available)),
            "requested": str(quantize_qty(requested)),
        },
    )


def _trace_fields(line: dict) -> dict:
    return {
        "batch_no": str(line.get("batch_no") or "").strip(),
        "serial_no": str(line.get("serial_no") or "").strip(),
        "heat_no": (str(line.get("heat_no")).strip() if line.get("heat_no") else None),
        "production_date": line.get("production_date"),
        "expiry_date": line.get("expiry_date"),
    }


VOUCHER_FIELDS = (
    "supplier_name",
    "purchase_order_no",
    "delivery_note_no",
    "acceptance_no",
    "acceptor",
    "qc_result",
    "manufacturer",
    "batch_no",
    "requisition_no",
    "work_package",
    "crew_name",
    "requester_name",
    "receiver_name",
    "signed_off",
    "scrap_weight",
    "scrap_assessed_value",
    "scrap_disposal_method",
    "scrap_recycler",
    "scrap_residual_value",
)


class WarehousePostingService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.scope = WarehouseScopeService(db, user)

    def _period_service(self):
        from app.services.warehouse.periods import WarehousePeriodService

        return WarehousePeriodService(self.db, self.user)

    async def find_by_idempotency(
        self, idempotency_key: str | None
    ) -> WarehouseDocument | None:
        if not idempotency_key:
            return None
        result = await self.db.execute(
            select(WarehouseDocument)
            .options(
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.material
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.source_warehouse
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.source_location
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.source_project
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.target_warehouse
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.target_location
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.target_project
                ),
            )
            .where(
                WarehouseDocument.created_by == self.user.id,
                WarehouseDocument.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def post_inbound(
        self,
        *,
        warehouse_id: int,
        location_id: int,
        project_id: int,
        occurred_on,
        handler: str,
        business_type: str,
        lines: Sequence[dict],
        reference_no: str | None = None,
        description: str | None = None,
        delivery_note_file: str | None = None,
        delivery_note_file_name: str | None = None,
        voucher: dict | None = None,
        idempotency_key: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WarehouseDocument:
        existing = await self.find_by_idempotency(idempotency_key)
        if existing:
            return existing
        await self.scope.assert_warehouse_access(
            warehouse_id, for_posting=True, action="入库"
        )
        document_lines = []
        for index, line in enumerate(lines, start=1):
            material = await self._assert_material_trace(line)
            qty = quantize_qty(line["quantity"], material.quantity_scale or 3)
            if qty <= ZERO:
                raise ValidationError(message="入库数量必须大于零")
            document_lines.append(
                {
                    "line_no": index,
                    "material_id": line["material_id"],
                    "quantity": qty,
                    "source_warehouse_id": None,
                    "source_location_id": None,
                    "source_project_id": None,
                    "target_warehouse_id": line.get("warehouse_id") or warehouse_id,
                    "target_location_id": line.get("location_id") or location_id,
                    "target_project_id": line.get("project_id") or project_id,
                    "description": line.get("description"),
                    **_trace_fields(line),
                }
            )
        await self._assert_target_dimensions(document_lines)
        await self.scope.assert_warehouses_access(
            [line["target_warehouse_id"] for line in document_lines],
            for_posting=True,
            action="入库",
        )
        await self._assert_no_active_counts(
            [line["target_warehouse_id"] for line in document_lines]
        )
        await self._period_service().assert_posting_allowed(occurred_on)
        return await self._create_and_post(
            document_type=DocumentType.INBOUND,
            business_type=business_type,
            occurred_on=occurred_on,
            handler=handler,
            reference_no=reference_no,
            description=description,
            delivery_note_file=delivery_note_file,
            delivery_note_file_name=delivery_note_file_name,
            voucher=voucher,
            idempotency_key=idempotency_key,
            lines=document_lines,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def post_outbound(
        self,
        *,
        warehouse_id: int,
        location_id: int,
        project_id: int,
        occurred_on,
        handler: str,
        business_type: str,
        lines: Sequence[dict],
        reference_no: str | None = None,
        description: str | None = None,
        scrap_basis_file: str | None = None,
        scrap_basis_file_name: str | None = None,
        voucher: dict | None = None,
        idempotency_key: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WarehouseDocument:
        existing = await self.find_by_idempotency(idempotency_key)
        if existing:
            return existing
        if business_type == "SCRAP_DISPOSAL" and not scrap_basis_file:
            raise ValidationError(message="选择废旧处理必须上传废旧处理依据文件")
        await self.scope.assert_warehouse_access(
            warehouse_id, for_posting=True, action="出库"
        )
        document_lines = []
        for index, line in enumerate(lines, start=1):
            material = await self._assert_material_trace(line)
            qty = quantize_qty(line["quantity"], material.quantity_scale or 3)
            if qty <= ZERO:
                raise ValidationError(message="出库数量必须大于零")
            document_lines.append(
                {
                    "line_no": index,
                    "material_id": line["material_id"],
                    "quantity": qty,
                    "source_warehouse_id": line.get("warehouse_id") or warehouse_id,
                    "source_location_id": line.get("location_id") or location_id,
                    "source_project_id": line.get("project_id") or project_id,
                    "target_warehouse_id": None,
                    "target_location_id": None,
                    "target_project_id": None,
                    "description": line.get("description"),
                    **_trace_fields(line),
                }
            )
        await self._assert_source_dimensions(document_lines)
        await self.scope.assert_warehouses_access(
            [line["source_warehouse_id"] for line in document_lines],
            for_posting=True,
            action="出库",
        )
        await self._assert_no_active_counts(
            [line["source_warehouse_id"] for line in document_lines]
        )
        await self._period_service().assert_posting_allowed(occurred_on)
        return await self._create_and_post(
            document_type=DocumentType.OUTBOUND,
            business_type=business_type,
            occurred_on=occurred_on,
            handler=handler,
            reference_no=reference_no,
            description=description,
            scrap_basis_file=scrap_basis_file,
            scrap_basis_file_name=scrap_basis_file_name,
            voucher=voucher,
            scrap_status=ScrapDisposalStatus.PENDING.value
            if business_type == "SCRAP_DISPOSAL"
            else None,
            idempotency_key=idempotency_key,
            lines=document_lines,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def post_transfer(
        self,
        *,
        occurred_on,
        handler: str,
        reference_no: str,
        lines: Sequence[dict],
        description: str | None = None,
        idempotency_key: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WarehouseDocument:
        existing = await self.find_by_idempotency(idempotency_key)
        if existing:
            return existing
        document_lines = []
        source_ids: list[int] = []
        for index, line in enumerate(lines, start=1):
            material = await self._assert_material_trace(line)
            qty = quantize_qty(line["quantity"], material.quantity_scale or 3)
            if qty <= ZERO:
                raise ValidationError(message="调拨数量必须大于零")
            source = (
                line["source_warehouse_id"],
                line["source_location_id"],
                line["source_project_id"],
                line["material_id"],
            )
            target = (
                line["target_warehouse_id"],
                line["target_location_id"],
                line["target_project_id"],
                line["material_id"],
            )
            if source == target:
                raise ValidationError(message="调出维度与调入维度不能完全相同")
            source_ids.append(line["source_warehouse_id"])
            document_lines.append(
                {
                    "line_no": index,
                    "material_id": line["material_id"],
                    "quantity": qty,
                    "source_warehouse_id": line["source_warehouse_id"],
                    "source_location_id": line["source_location_id"],
                    "source_project_id": line["source_project_id"],
                    "target_warehouse_id": line["target_warehouse_id"],
                    "target_location_id": line["target_location_id"],
                    "target_project_id": line["target_project_id"],
                    "description": line.get("description"),
                    **_trace_fields(line),
                }
            )
        await self.scope.assert_warehouses_access(
            source_ids + [line["target_warehouse_id"] for line in document_lines],
            for_posting=True,
            action="调拨",
        )
        await self._assert_source_dimensions(document_lines)
        await self._assert_target_dimensions(document_lines)
        await self._assert_no_active_counts(
            source_ids + [line["target_warehouse_id"] for line in document_lines]
        )
        await self._period_service().assert_posting_allowed(occurred_on)
        return await self._create_and_post(
            document_type=DocumentType.TRANSFER,
            business_type="TRANSFER",
            occurred_on=occurred_on,
            handler=handler,
            reference_no=reference_no,
            description=description,
            idempotency_key=idempotency_key,
            lines=document_lines,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def post_count_adjustment(
        self,
        *,
        occurred_on,
        handler: str,
        reference_no: str,
        lines: Sequence[dict],
        description: str | None = None,
        idempotency_key: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        ignore_count_id: int | None = None,
    ) -> WarehouseDocument:
        existing = await self.find_by_idempotency(idempotency_key)
        if existing:
            return existing
        document_lines = []
        warehouse_ids: list[int] = []
        for index, line in enumerate(lines, start=1):
            qty = quantize_qty(line["quantity"])
            if qty == ZERO:
                continue
            if qty > ZERO:
                warehouse_ids.append(line["warehouse_id"])
                document_lines.append(
                    {
                        "line_no": index,
                        "material_id": line["material_id"],
                        "quantity": qty,
                        "source_warehouse_id": None,
                        "source_location_id": None,
                        "source_project_id": None,
                        "target_warehouse_id": line["warehouse_id"],
                        "target_location_id": line["location_id"],
                        "target_project_id": line["project_id"],
                        "description": line.get("description") or "盘盈",
                        **_trace_fields(line),
                    }
                )
            else:
                warehouse_ids.append(line["warehouse_id"])
                document_lines.append(
                    {
                        "line_no": index,
                        "material_id": line["material_id"],
                        "quantity": -qty,
                        "source_warehouse_id": line["warehouse_id"],
                        "source_location_id": line["location_id"],
                        "source_project_id": line["project_id"],
                        "target_warehouse_id": None,
                        "target_location_id": None,
                        "target_project_id": None,
                        "description": line.get("description") or "盘亏",
                        **_trace_fields(line),
                    }
                )
        if not document_lines:
            raise ValidationError(message="没有需要调整的盘点差异")
        await self.scope.assert_warehouses_access(
            warehouse_ids, for_posting=True, action="盘点确认"
        )
        await self._assert_no_active_counts(
            warehouse_ids, ignore_count_id=ignore_count_id
        )
        await self._assert_source_dimensions(
            [line for line in document_lines if line["source_warehouse_id"]]
        )
        await self._assert_target_dimensions(
            [line for line in document_lines if line["target_warehouse_id"]]
        )
        await self._period_service().assert_posting_allowed(occurred_on)
        return await self._create_and_post(
            document_type=DocumentType.COUNT_ADJUSTMENT,
            business_type="COUNT_ADJUSTMENT",
            occurred_on=occurred_on,
            handler=handler,
            reference_no=reference_no,
            description=description,
            idempotency_key=idempotency_key,
            lines=document_lines,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def void_document(
        self,
        document_id: int,
        reason: str,
        *,
        idempotency_key: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WarehouseDocument:
        existing = await self.find_by_idempotency(idempotency_key)
        if existing:
            return existing

        original = await self.get_document(document_id, for_update=True)
        if original.document_type == DocumentType.REVERSAL.value:
            raise ValidationError(message="冲销单不能再次冲销")
        if original.status == DocumentStatus.VOIDED.value:
            raise AppException(
                error_code=ErrorCode.DOCUMENT_ALREADY_VOIDED,
                message="单据已冲销",
                status_code=409,
            )
        if original.status != DocumentStatus.POSTED.value:
            raise AppException(
                error_code=ErrorCode.DOCUMENT_NOT_POSTED,
                message="只能冲销已过账单据",
                status_code=409,
            )

        warehouse_ids = set()
        reversal_lines = []
        for line in original.lines:
            if line.source_warehouse_id:
                warehouse_ids.add(line.source_warehouse_id)
            if line.target_warehouse_id:
                warehouse_ids.add(line.target_warehouse_id)
            reversal_lines.append(
                {
                    "line_no": line.line_no,
                    "material_id": line.material_id,
                    "quantity": quantize_qty(line.quantity),
                    "source_warehouse_id": line.target_warehouse_id,
                    "source_location_id": line.target_location_id,
                    "source_project_id": line.target_project_id,
                    "target_warehouse_id": line.source_warehouse_id,
                    "target_location_id": line.source_location_id,
                    "target_project_id": line.source_project_id,
                    "original_document_line_id": line.id,
                    "description": f"冲销 {original.document_no} 第 {line.line_no} 行",
                    "batch_no": line.batch_no or "",
                    "serial_no": line.serial_no or "",
                    "heat_no": line.heat_no,
                    "production_date": line.production_date,
                    "expiry_date": line.expiry_date,
                }
            )
        await self.scope.assert_warehouses_access(
            warehouse_ids, for_posting=True, action="冲销"
        )
        await self._assert_no_active_counts(warehouse_ids)
        await self._period_service().assert_posting_allowed(original.occurred_on)

        reversal = await self._create_and_post(
            document_type=DocumentType.REVERSAL,
            business_type="REVERSAL",
            occurred_on=original.occurred_on,
            handler=original.handler,
            reference_no=original.document_no,
            description=reason,
            idempotency_key=idempotency_key,
            lines=reversal_lines,
            reversed_document_id=original.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        now = datetime.now(timezone.utc)
        original.status = DocumentStatus.VOIDED.value
        original.voided_by = self.user.id
        original.voided_at = now
        original.void_reason = reason
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE,
            ResourceType.WAREHOUSE_DOCUMENT,
            resource_id=original.id,
            resource_name=original.document_no,
            description=f"冲销单据 {original.document_no}: {reason}",
            old_values={"status": DocumentStatus.POSTED.value},
            new_values={
                "status": DocumentStatus.VOIDED.value,
                "reversal_id": reversal.id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return reversal

    async def get_document(
        self, document_id: int, *, for_update: bool = False
    ) -> WarehouseDocument:
        statement = (
            select(WarehouseDocument)
            .options(
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.material
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.source_warehouse
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.source_location
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.source_project
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.target_warehouse
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.target_location
                ),
                selectinload(WarehouseDocument.lines).selectinload(
                    WarehouseDocumentLine.target_project
                ),
                selectinload(WarehouseDocument.supplements),
            )
            .where(WarehouseDocument.id == document_id)
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self.db.execute(statement)
        document = result.scalar_one_or_none()
        if document is None:
            raise AppException(
                error_code=ErrorCode.RECORD_NOT_FOUND,
                message="单据不存在",
                status_code=404,
            )
        return document

    async def _assert_no_active_counts(
        self, warehouse_ids: Iterable[int], *, ignore_count_id: int | None = None
    ) -> None:
        ids = {warehouse_id for warehouse_id in warehouse_ids if warehouse_id}
        if not ids:
            return
        await self.lock_warehouses(ids)
        query = select(WarehouseCount.id).where(
            WarehouseCount.warehouse_id.in_(ids),
            WarehouseCount.status.in_(
                (
                    CountStatus.DRAFT.value,
                    CountStatus.ENTERED.value,
                    CountStatus.REVIEWED.value,
                )
            ),
        )
        if ignore_count_id is not None:
            query = query.where(WarehouseCount.id != ignore_count_id)
        result = await self.db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            raise AppException(
                error_code=ErrorCode.WAREHOUSE_CONFLICT,
                message="盘点期间禁止库存过账",
                detail="请先完成或作废相关盘点",
                status_code=409,
            )

    async def lock_warehouses(self, warehouse_ids: Iterable[int]) -> None:
        ids = sorted({warehouse_id for warehouse_id in warehouse_ids if warehouse_id})
        for warehouse_id in ids:
            result = await self.db.execute(
                select(Warehouse.id)
                .where(Warehouse.id == warehouse_id)
                .with_for_update()
            )
            if result.scalar_one_or_none() is None:
                raise AppException(
                    error_code=ErrorCode.WAREHOUSE_NOT_FOUND,
                    message="库房不存在",
                    status_code=404,
                )

    async def get_available(self, key: StockKey) -> Decimal:
        query = select(func.coalesce(func.sum(WarehouseStockBalance.quantity), 0)).where(
            WarehouseStockBalance.warehouse_id == key.warehouse_id,
            WarehouseStockBalance.location_id == key.location_id,
            WarehouseStockBalance.project_id == key.project_id,
            WarehouseStockBalance.material_id == key.material_id,
        )
        if key.batch_no:
            query = query.where(WarehouseStockBalance.batch_no == key.batch_no)
        if key.serial_no:
            query = query.where(WarehouseStockBalance.serial_no == key.serial_no)
        value = (await self.db.execute(query)).scalar_one()
        return quantize_qty(value or ZERO)

    async def rebuild_balances(
        self,
        *,
        repair: bool = False,
        reason: str | None = None,
    ) -> dict:
        if repair and not (
            self.user.is_superuser
            or has_permission(self.user, Permission.REPAIR_WAREHOUSE_BALANCES)
        ):
            raise AppException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message="只有库房管理员可以执行库存对账修复",
                status_code=403,
            )
        if repair and not (reason or "").strip():
            raise ValidationError(message="库存对账修复必须填写原因")
        totals = await self.db.execute(
            select(
                WarehouseLedgerEntry.warehouse_id,
                WarehouseLedgerEntry.location_id,
                WarehouseLedgerEntry.project_id,
                WarehouseLedgerEntry.material_id,
                WarehouseLedgerEntry.batch_no,
                WarehouseLedgerEntry.serial_no,
                func.coalesce(func.sum(WarehouseLedgerEntry.quantity_delta), 0),
            ).group_by(
                WarehouseLedgerEntry.warehouse_id,
                WarehouseLedgerEntry.location_id,
                WarehouseLedgerEntry.project_id,
                WarehouseLedgerEntry.material_id,
                WarehouseLedgerEntry.batch_no,
                WarehouseLedgerEntry.serial_no,
            )
        )
        ledger_map = {
            StockKey(row[0], row[1], row[2], row[3], row[4] or "", row[5] or ""): quantize_qty(row[6])
            for row in totals.all()
        }
        existing = await self.db.execute(
            select(WarehouseStockBalance).with_for_update()
        )
        balances = existing.scalars().all()
        mismatches = 0
        differences: list[dict] = []
        seen: set[StockKey] = set()
        for balance in balances:
            key = StockKey(
                balance.warehouse_id,
                balance.location_id,
                balance.project_id,
                balance.material_id,
                balance.batch_no or "",
                balance.serial_no or "",
            )
            seen.add(key)
            expected = ledger_map.get(key, ZERO)
            current = quantize_qty(balance.quantity)
            if current != expected:
                mismatches += 1
                differences.append(
                    {
                        "warehouse_id": key.warehouse_id,
                        "location_id": key.location_id,
                        "project_id": key.project_id,
                        "material_id": key.material_id,
                        "batch_no": key.batch_no,
                        "serial_no": key.serial_no,
                        "current": str(current),
                        "expected": str(expected),
                    }
                )
                if repair:
                    balance.quantity = expected
                    balance.version = int(balance.version or 1) + 1
        for key, expected in ledger_map.items():
            if key in seen:
                continue
            mismatches += 1
            differences.append(
                {
                    "warehouse_id": key.warehouse_id,
                    "location_id": key.location_id,
                    "project_id": key.project_id,
                    "material_id": key.material_id,
                    "batch_no": key.batch_no,
                    "serial_no": key.serial_no,
                    "current": str(ZERO),
                    "expected": str(expected),
                }
            )
            if repair:
                self.db.add(
                    WarehouseStockBalance(
                        warehouse_id=key.warehouse_id,
                        location_id=key.location_id,
                        project_id=key.project_id,
                        material_id=key.material_id,
                        batch_no=key.batch_no,
                        serial_no=key.serial_no,
                        quantity=expected,
                        version=1,
                    )
                )
        record = WarehouseBalanceRepair(
            dry_run=not repair,
            repaired=bool(repair),
            reason=(reason or "").strip() or None,
            dimensions=len(set(seen) | set(ledger_map)),
            mismatches=mismatches,
            differences=json.dumps(differences, ensure_ascii=False),
            created_by=self.user.id,
        )
        self.db.add(record)
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.UPDATE if repair else AuditAction.VIEW,
            ResourceType.WAREHOUSE_BALANCE_REPAIR,
            resource_id=record.id,
            resource_name=f"mismatches={mismatches}",
            description=(
                f"{'执行' if repair else '预览'}库存对账修复，差异 {mismatches} 条"
            ),
            new_values={
                "repair": repair,
                "mismatches": mismatches,
                "reason": record.reason,
            },
        )
        return {
            "id": record.id,
            "dimensions": record.dimensions,
            "mismatches": mismatches,
            "repaired": bool(repair),
            "dry_run": not repair,
            "reason": record.reason,
            "differences": differences,
        }

    async def _create_and_post(
        self,
        *,
        document_type: DocumentType,
        business_type: str | None,
        occurred_on,
        handler: str,
        reference_no: str | None,
        description: str | None,
        idempotency_key: str | None,
        lines: Sequence[dict],
        reversed_document_id: int | None = None,
        delivery_note_file: str | None = None,
        delivery_note_file_name: str | None = None,
        scrap_basis_file: str | None = None,
        scrap_basis_file_name: str | None = None,
        voucher: dict | None = None,
        scrap_status: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WarehouseDocument:
        now = datetime.now(timezone.utc)
        document_no = await generate_document_no(self.db, document_type, occurred_on)
        voucher_values = self._voucher_values(voucher)
        document = WarehouseDocument(
            document_no=document_no,
            document_type=document_type.value,
            status=DocumentStatus.POSTED.value,
            occurred_on=occurred_on,
            business_type=business_type,
            reference_no=reference_no,
            description=description,
            handler=handler,
            idempotency_key=idempotency_key,
            delivery_note_file=delivery_note_file,
            delivery_note_file_name=delivery_note_file_name,
            scrap_basis_file=scrap_basis_file,
            scrap_basis_file_name=scrap_basis_file_name,
            scrap_status=scrap_status,
            created_by=self.user.id,
            posted_by=self.user.id,
            posted_at=now,
            reversed_document_id=reversed_document_id,
            **voucher_values,
        )
        self.db.add(document)
        await self.db.flush()

        created_lines: list[WarehouseDocumentLine] = []
        for line in lines:
            await self._assert_material_trace(line)
            row = WarehouseDocumentLine(
                document_id=document.id,
                line_no=line["line_no"],
                material_id=line["material_id"],
                quantity=line["quantity"],
                source_warehouse_id=line.get("source_warehouse_id"),
                source_location_id=line.get("source_location_id"),
                source_project_id=line.get("source_project_id"),
                target_warehouse_id=line.get("target_warehouse_id"),
                target_location_id=line.get("target_location_id"),
                target_project_id=line.get("target_project_id"),
                original_document_line_id=line.get("original_document_line_id"),
                batch_no=str(line.get("batch_no") or ""),
                serial_no=str(line.get("serial_no") or ""),
                heat_no=line.get("heat_no"),
                production_date=line.get("production_date"),
                expiry_date=line.get("expiry_date"),
                description=line.get("description"),
            )
            self.db.add(row)
            created_lines.append(row)
        await self.db.flush()

        planned = self._plan_deltas(created_lines)
        await self._apply_deltas(planned, occurred_on, created_lines)

        await create_audit_log(
            self.db,
            self.user,
            AuditAction.CREATE,
            ResourceType.WAREHOUSE_DOCUMENT,
            resource_id=document.id,
            resource_name=document.document_no,
            description=f"过账{document_type.value} {document.document_no}",
            new_values={
                "document_no": document.document_no,
                "document_type": document.document_type,
                "business_type": document.business_type,
                "lines": len(created_lines),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.db.flush()
        return await self.get_document(document.id)

    def _plan_deltas(
        self, lines: Iterable[WarehouseDocumentLine]
    ) -> list[PlannedDelta]:
        planned: list[PlannedDelta] = []
        for line in lines:
            qty = quantize_qty(line.quantity)
            if line.source_warehouse_id:
                planned.append(
                    PlannedDelta(
                        key=StockKey(
                            line.source_warehouse_id,
                            line.source_location_id,
                            line.source_project_id,
                            line.material_id,
                            line.batch_no or "",
                            line.serial_no or "",
                        ),
                        quantity_delta=-qty,
                        document_line_id=line.id,
                    )
                )
            if line.target_warehouse_id:
                planned.append(
                    PlannedDelta(
                        key=StockKey(
                            line.target_warehouse_id,
                            line.target_location_id,
                            line.target_project_id,
                            line.material_id,
                            line.batch_no or "",
                            line.serial_no or "",
                        ),
                        quantity_delta=qty,
                        document_line_id=line.id,
                    )
                )
        return planned

    async def _apply_deltas(
        self,
        planned: Sequence[PlannedDelta],
        occurred_on,
        created_lines: Sequence[WarehouseDocumentLine],
    ) -> None:
        keys = sorted({item.key for item in planned})
        balances = await self._lock_balances(keys)
        line_map = {line.id: line for line in created_lines}
        for item in planned:
            balance = balances[item.key]
            next_qty = quantize_qty(balance.quantity) + item.quantity_delta
            if next_qty < ZERO:
                raise _insufficient_stock_error(
                    item.key,
                    available=quantize_qty(balance.quantity),
                    requested=-item.quantity_delta
                    if item.quantity_delta < ZERO
                    else item.quantity_delta,
                )
            balance.quantity = next_qty
            balance.version = int(balance.version or 1) + 1
            line = line_map[item.document_line_id]
            if item.quantity_delta > ZERO and line.expiry_date:
                balance.expiry_date = line.expiry_date
            self.db.add(
                WarehouseLedgerEntry(
                    document_id=line.document_id,
                    document_line_id=item.document_line_id,
                    warehouse_id=item.key.warehouse_id,
                    location_id=item.key.location_id,
                    project_id=item.key.project_id,
                    material_id=item.key.material_id,
                    batch_no=item.key.batch_no,
                    serial_no=item.key.serial_no,
                    expiry_date=line.expiry_date,
                    quantity_delta=item.quantity_delta,
                    occurred_on=occurred_on,
                )
            )
        await self.db.flush()

    async def _lock_balances(
        self, keys: Sequence[StockKey]
    ) -> dict[StockKey, WarehouseStockBalance]:
        balances: dict[StockKey, WarehouseStockBalance] = {}
        for key in keys:
            stmt = (
                insert(WarehouseStockBalance)
                .values(
                    warehouse_id=key.warehouse_id,
                    location_id=key.location_id,
                    project_id=key.project_id,
                    material_id=key.material_id,
                    batch_no=key.batch_no,
                    serial_no=key.serial_no,
                    quantity=ZERO,
                    version=1,
                )
                .on_conflict_do_nothing(
                    index_elements=[
                        "warehouse_id",
                        "location_id",
                        "project_id",
                        "material_id",
                        "batch_no",
                        "serial_no",
                    ]
                )
            )
            await self.db.execute(stmt)
            result = await self.db.execute(
                select(WarehouseStockBalance)
                .where(
                    WarehouseStockBalance.warehouse_id == key.warehouse_id,
                    WarehouseStockBalance.location_id == key.location_id,
                    WarehouseStockBalance.project_id == key.project_id,
                    WarehouseStockBalance.material_id == key.material_id,
                    WarehouseStockBalance.batch_no == key.batch_no,
                    WarehouseStockBalance.serial_no == key.serial_no,
                )
                .with_for_update()
            )
            balances[key] = result.scalar_one()
        return balances

    async def _assert_material(self, material_id: int) -> WarehouseMaterial:
        material = await self.db.get(WarehouseMaterial, material_id)
        if material is None or not material.is_active:
            raise AppException(
                error_code=ErrorCode.RECORD_NOT_FOUND,
                message="物资不存在或已归档",
                status_code=404,
            )
        return material

    async def _assert_material_trace(self, line: dict) -> WarehouseMaterial:
        material = await self._assert_material(line["material_id"])
        raw_quantity = Decimal(line["quantity"])
        normalized_quantity = quantize_qty(raw_quantity, material.quantity_scale or 3)
        if raw_quantity != normalized_quantity:
            raise ValidationError(
                message=f"物资 {material.code} 数量最多保留 {material.quantity_scale or 3} 位小数"
            )
        if material.tracks_batch and not str(line.get("batch_no") or "").strip():
            raise ValidationError(message=f"物资 {material.code} 必须填写批次号")
        if material.tracks_serial and not str(line.get("serial_no") or "").strip():
            raise ValidationError(message=f"物资 {material.code} 必须填写序列号")
        if material.tracks_serial and normalized_quantity != Decimal("1"):
            raise ValidationError(message=f"序列号物资 {material.code} 每行数量必须为 1")
        return material

    async def _assert_source_dimensions(self, lines: Sequence[dict]) -> None:
        for line in lines:
            await self._assert_dimension(
                line["source_warehouse_id"],
                line["source_location_id"],
                line["source_project_id"],
            )

    async def _assert_target_dimensions(self, lines: Sequence[dict]) -> None:
        for line in lines:
            await self._assert_dimension(
                line["target_warehouse_id"],
                line["target_location_id"],
                line["target_project_id"],
            )

    async def _assert_dimension(
        self,
        warehouse_id: int | None,
        location_id: int | None,
        project_id: int | None,
    ) -> None:
        if not warehouse_id or not location_id or not project_id:
            raise ValidationError(message="库存维度不完整")
        warehouse = await self.db.get(Warehouse, warehouse_id)
        if warehouse is None or not warehouse.is_active:
            raise ValidationError(message="库房不存在或已停用")
        location = await self.db.get(WarehouseLocation, location_id)
        if (
            location is None
            or not location.is_active
            or location.warehouse_id != warehouse_id
        ):
            raise ValidationError(message="货位不属于该库房或已停用")
        project = await self.db.get(WarehouseProject, project_id)
        if project is None or not project.is_active:
            raise ValidationError(message="项目不存在或已停用")

    @staticmethod
    def _voucher_values(voucher: dict | None) -> dict:
        payload = voucher or {}
        values: dict = {}
        for field in VOUCHER_FIELDS:
            if field in payload:
                values[field] = payload[field]
        if "signed_off" in values:
            values["signed_off"] = bool(values["signed_off"])
        for money_field in (
            "scrap_assessed_value",
            "scrap_residual_value",
        ):
            if values.get(money_field) is not None:
                amount = Decimal(values[money_field]).quantize(Decimal("0.01"))
                if amount < ZERO:
                    raise ValidationError(message="残值或评估价值不能为负数")
                values[money_field] = amount
        if values.get("scrap_weight") is not None:
            weight = quantize_qty(values["scrap_weight"])
            if weight < ZERO:
                raise ValidationError(message="过磅重量不能为负数")
            values["scrap_weight"] = weight
        return values

    async def settle_scrap(
        self,
        document_id: int,
        *,
        scrap_weight: Decimal | None = None,
        scrap_assessed_value: Decimal | None = None,
        scrap_disposal_method: str | None = None,
        scrap_recycler: str | None = None,
        scrap_residual_value: Decimal | None = None,
        scrap_status: str | None = None,
    ) -> WarehouseDocument:
        if not (
            self.user.is_superuser
            or has_permission(self.user, Permission.SETTLE_WAREHOUSE_SCRAP)
        ):
            raise AppException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message="无权核销废旧处置",
                status_code=403,
            )
        document = await self.get_document(document_id, for_update=True)
        warehouse_ids = {
            warehouse_id
            for line in document.lines
            for warehouse_id in (line.source_warehouse_id, line.target_warehouse_id)
            if warehouse_id
        }
        await self.scope.assert_warehouses_access(warehouse_ids, action="废旧处置核销")
        if document.business_type != "SCRAP_DISPOSAL":
            raise ValidationError(message="仅废旧处理单据可以核销闭环")
        if document.status != DocumentStatus.POSTED.value:
            raise ValidationError(message="已冲销单据不能核销废旧处置")
        updates = self._voucher_values(
            {
                "scrap_weight": scrap_weight,
                "scrap_assessed_value": scrap_assessed_value,
                "scrap_disposal_method": scrap_disposal_method,
                "scrap_recycler": scrap_recycler,
                "scrap_residual_value": scrap_residual_value,
            }
        )
        for key, value in updates.items():
            if value is not None:
                setattr(document, key, value)
        next_status = scrap_status or ScrapDisposalStatus.SETTLED.value
        if next_status not in {item.value for item in ScrapDisposalStatus}:
            raise ValidationError(message="废旧处置状态无效")
        current_status = document.scrap_status or ScrapDisposalStatus.PENDING.value
        allowed_transitions = {
            ScrapDisposalStatus.PENDING.value: {ScrapDisposalStatus.APPROVED.value, ScrapDisposalStatus.SETTLED.value, ScrapDisposalStatus.VOIDED.value},
            ScrapDisposalStatus.APPROVED.value: {ScrapDisposalStatus.WEIGHED.value, ScrapDisposalStatus.VOIDED.value},
            ScrapDisposalStatus.WEIGHED.value: {ScrapDisposalStatus.SETTLED.value, ScrapDisposalStatus.VOIDED.value},
            ScrapDisposalStatus.SETTLED.value: set(),
            ScrapDisposalStatus.VOIDED.value: set(),
        }
        if next_status != current_status and next_status not in allowed_transitions[current_status]:
            raise ValidationError(message=f"废旧处置不能从 {current_status} 直接变更为 {next_status}")
        if next_status == ScrapDisposalStatus.WEIGHED.value and document.scrap_weight is None:
            raise ValidationError(message="过磅阶段必须填写重量")
        if next_status == ScrapDisposalStatus.SETTLED.value:
            if not document.scrap_basis_file:
                raise ValidationError(message="废旧核销必须保留依据文件")
            if document.scrap_weight is None:
                raise ValidationError(message="废旧核销必须填写过磅重量")
            if not document.scrap_recycler:
                raise ValidationError(message="废旧核销必须填写回收单位")
            if document.scrap_assessed_value is None or document.scrap_residual_value is None:
                raise ValidationError(message="废旧核销必须填写评估价值和残值")
            document.scrap_settled_at = datetime.now(timezone.utc)
            document.scrap_settled_by = self.user.id
        document.scrap_status = next_status
        await self.db.flush()
        await create_audit_log(
            self.db,
            self.user,
            AuditAction.APPROVE,
            ResourceType.WAREHOUSE_DOCUMENT,
            resource_id=document.id,
            resource_name=document.document_no,
            description=f"废旧处置状态变更为 {next_status}",
            new_values={"scrap_status": next_status},
        )
        return await self.get_document(document.id)
