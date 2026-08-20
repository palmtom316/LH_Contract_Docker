"""Warehouse query helpers and response builders."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ValidationError
from app.core.timezone import business_today
from app.models.warehouse import (
    Warehouse,
    WarehouseDocument,
    WarehouseDocumentLine,
    WarehouseLedgerEntry,
    WarehouseMaterial,
    WarehouseProject,
    WarehouseStockBalance,
    WarehouseUnit,
    WarehouseUnitConversion,
)
from app.schemas.warehouse import (
    DocumentLineResponse,
    DocumentResponse,
    LedgerEntryResponse,
    StockBalanceResponse,
)
from app.services.warehouse.scope import WarehouseScopeService


def serialize_document(document: WarehouseDocument) -> DocumentResponse:
    lines = []
    for line in document.lines:
        lines.append(
            DocumentLineResponse(
                id=line.id,
                line_no=line.line_no,
                material_id=line.material_id,
                material_code=line.material.code if line.material else None,
                material_name=line.material.name if line.material else None,
                material_unit=line.material.unit if line.material else None,
                quantity=line.quantity,
                batch_no=line.batch_no or None,
                serial_no=line.serial_no or None,
                heat_no=line.heat_no,
                production_date=line.production_date,
                expiry_date=line.expiry_date,
                source_warehouse_id=line.source_warehouse_id,
                source_location_id=line.source_location_id,
                source_project_id=line.source_project_id,
                target_warehouse_id=line.target_warehouse_id,
                target_location_id=line.target_location_id,
                target_project_id=line.target_project_id,
                source_warehouse_name=line.source_warehouse.name
                if line.source_warehouse
                else None,
                source_location_name=line.source_location.name
                if line.source_location
                else None,
                source_project_name=line.source_project.name
                if line.source_project
                else None,
                target_warehouse_name=line.target_warehouse.name
                if line.target_warehouse
                else None,
                target_location_name=line.target_location.name
                if line.target_location
                else None,
                target_project_name=line.target_project.name
                if line.target_project
                else None,
                description=line.description,
            )
        )
    return DocumentResponse(
        id=document.id,
        document_no=document.document_no,
        document_type=document.document_type,
        status=document.status,
        occurred_on=document.occurred_on,
        business_type=document.business_type,
        reference_no=document.reference_no,
        description=document.description,
        handler=document.handler,
        created_by=document.created_by,
        posted_by=document.posted_by,
        voided_by=document.voided_by,
        created_at=document.created_at,
        posted_at=document.posted_at,
        voided_at=document.voided_at,
        void_reason=document.void_reason,
        delivery_note_file=document.delivery_note_file,
        delivery_note_file_name=document.delivery_note_file_name,
        scrap_basis_file=document.scrap_basis_file,
        scrap_basis_file_name=document.scrap_basis_file_name,
        supplier_name=document.supplier_name,
        purchase_order_no=document.purchase_order_no,
        delivery_note_no=document.delivery_note_no,
        acceptance_no=document.acceptance_no,
        acceptor=document.acceptor,
        qc_result=document.qc_result,
        manufacturer=document.manufacturer,
        batch_no=document.batch_no,
        requisition_no=document.requisition_no,
        work_package=document.work_package,
        crew_name=document.crew_name,
        requester_name=document.requester_name,
        receiver_name=document.receiver_name,
        signed_off=bool(document.signed_off),
        scrap_status=document.scrap_status,
        scrap_weight=document.scrap_weight,
        scrap_assessed_value=document.scrap_assessed_value,
        scrap_disposal_method=document.scrap_disposal_method,
        scrap_recycler=document.scrap_recycler,
        scrap_residual_value=document.scrap_residual_value,
        scrap_settled_at=document.scrap_settled_at,
        reversed_document_id=document.reversed_document_id,
        lines=lines,
    )


def serialize_balance(row: WarehouseStockBalance) -> StockBalanceResponse:
    return StockBalanceResponse(
        warehouse_id=row.warehouse_id,
        location_id=row.location_id,
        project_id=row.project_id,
        material_id=row.material_id,
        batch_no=row.batch_no or None,
        serial_no=row.serial_no or None,
        expiry_date=row.expiry_date,
        quantity=row.quantity,
        minimum_stock=row.material.minimum_stock if row.material else Decimal(0),
        version=row.version,
        warehouse_code=row.warehouse.code if row.warehouse else None,
        warehouse_name=row.warehouse.name if row.warehouse else None,
        location_code=row.location.code if row.location else None,
        location_name=row.location.name if row.location else None,
        project_code=row.project.code if row.project else None,
        project_name=row.project.name if row.project else None,
        material_code=row.material.code if row.material else None,
        material_name=row.material.name if row.material else None,
        material_unit=row.material.unit if row.material else None,
        supply_type=row.material.supply_type if row.material else None,
        condition=row.material.condition if row.material else None,
        category=row.material.category if row.material else None,
        updated_at=row.updated_at,
    )


class WarehouseQueryService:
    def __init__(self, db: AsyncSession, scope: WarehouseScopeService):
        self.db = db
        self.scope = scope

    async def list_balances(
        self,
        *,
        warehouse_id: int | None = None,
        location_id: int | None = None,
        project_id: int | None = None,
        material_id: int | None = None,
        supply_type: str | None = None,
        condition: str | None = None,
        category: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
        include_zero: bool = False,
        for_posting: bool = False,
    ) -> tuple[list[WarehouseStockBalance], int]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=for_posting)
        query = (
            select(WarehouseStockBalance)
            .options(
                selectinload(WarehouseStockBalance.warehouse),
                selectinload(WarehouseStockBalance.location),
                selectinload(WarehouseStockBalance.project),
                selectinload(WarehouseStockBalance.material),
            )
            .join(
                WarehouseMaterial,
                WarehouseMaterial.id == WarehouseStockBalance.material_id,
            )
        )
        count_query = select(func.count(WarehouseStockBalance.id)).join(
            WarehouseMaterial, WarehouseMaterial.id == WarehouseStockBalance.material_id
        )
        if allowed is not None:
            query = query.where(WarehouseStockBalance.warehouse_id.in_(allowed or [-1]))
            count_query = count_query.where(
                WarehouseStockBalance.warehouse_id.in_(allowed or [-1])
            )
        if warehouse_id:
            query = query.where(WarehouseStockBalance.warehouse_id == warehouse_id)
            count_query = count_query.where(
                WarehouseStockBalance.warehouse_id == warehouse_id
            )
        if location_id:
            query = query.where(WarehouseStockBalance.location_id == location_id)
            count_query = count_query.where(
                WarehouseStockBalance.location_id == location_id
            )
        if project_id:
            query = query.where(WarehouseStockBalance.project_id == project_id)
            count_query = count_query.where(
                WarehouseStockBalance.project_id == project_id
            )
        if material_id:
            query = query.where(WarehouseStockBalance.material_id == material_id)
            count_query = count_query.where(
                WarehouseStockBalance.material_id == material_id
            )
        if supply_type:
            query = query.where(WarehouseMaterial.supply_type == supply_type)
            count_query = count_query.where(
                WarehouseMaterial.supply_type == supply_type
            )
        if condition:
            query = query.where(WarehouseMaterial.condition == condition)
            count_query = count_query.where(WarehouseMaterial.condition == condition)
        if category:
            query = query.where(WarehouseMaterial.category == category)
            count_query = count_query.where(WarehouseMaterial.category == category)
        if q:
            like = f"%{q.strip()}%"
            query = query.where(
                WarehouseMaterial.code.ilike(like) | WarehouseMaterial.name.ilike(like)
            )
            count_query = count_query.where(
                WarehouseMaterial.code.ilike(like) | WarehouseMaterial.name.ilike(like)
            )
        if not include_zero:
            query = query.where(WarehouseStockBalance.quantity > 0)
            count_query = count_query.where(WarehouseStockBalance.quantity > 0)
        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(WarehouseStockBalance.warehouse_id, WarehouseMaterial.code)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().unique().all()), int(total)

    async def list_documents(
        self,
        *,
        document_type: str | None = None,
        status: str | None = None,
        business_type: str | None = None,
        warehouse_id: int | None = None,
        material_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WarehouseDocument], int]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=False)
        query = (
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
            .join(
                WarehouseDocumentLine,
                WarehouseDocumentLine.document_id == WarehouseDocument.id,
            )
        )
        conditions = []
        if allowed is not None:
            conditions.append(
                (WarehouseDocumentLine.source_warehouse_id.in_(allowed or [-1]))
                | (WarehouseDocumentLine.target_warehouse_id.in_(allowed or [-1]))
            )
        if document_type:
            conditions.append(WarehouseDocument.document_type == document_type)
        if status:
            conditions.append(WarehouseDocument.status == status)
        if business_type:
            conditions.append(WarehouseDocument.business_type == business_type)
        if warehouse_id:
            conditions.append(
                (WarehouseDocumentLine.source_warehouse_id == warehouse_id)
                | (WarehouseDocumentLine.target_warehouse_id == warehouse_id)
            )
        if material_id:
            conditions.append(WarehouseDocumentLine.material_id == material_id)
        if start_date:
            conditions.append(WarehouseDocument.occurred_on >= start_date)
        if end_date:
            conditions.append(WarehouseDocument.occurred_on <= end_date)
        if conditions:
            for cond in conditions:
                query = query.where(cond)
        query = query.distinct()
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(
                WarehouseDocument.occurred_on.desc(), WarehouseDocument.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().unique().all()), int(total)

    async def list_ledger(
        self,
        *,
        warehouse_id: int | None = None,
        location_id: int | None = None,
        project_id: int | None = None,
        material_id: int | None = None,
        document_type: str | None = None,
        business_type: str | None = None,
        category: str | None = None,
        supply_type: str | None = None,
        condition: str | None = None,
        handler: str | None = None,
        q: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[WarehouseLedgerEntry], int]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=False)
        query = (
            select(WarehouseLedgerEntry)
            .options(
                selectinload(WarehouseLedgerEntry.document),
                selectinload(WarehouseLedgerEntry.warehouse),
                selectinload(WarehouseLedgerEntry.location),
                selectinload(WarehouseLedgerEntry.project),
                selectinload(WarehouseLedgerEntry.material),
            )
            .join(WarehouseDocument, WarehouseDocument.id == WarehouseLedgerEntry.document_id)
            .join(WarehouseMaterial, WarehouseMaterial.id == WarehouseLedgerEntry.material_id)
        )
        count_query = (
            select(func.count(WarehouseLedgerEntry.id))
            .join(WarehouseDocument, WarehouseDocument.id == WarehouseLedgerEntry.document_id)
            .join(WarehouseMaterial, WarehouseMaterial.id == WarehouseLedgerEntry.material_id)
        )
        if allowed is not None:
            query = query.where(WarehouseLedgerEntry.warehouse_id.in_(allowed or [-1]))
            count_query = count_query.where(
                WarehouseLedgerEntry.warehouse_id.in_(allowed or [-1])
            )
        if warehouse_id:
            query = query.where(WarehouseLedgerEntry.warehouse_id == warehouse_id)
            count_query = count_query.where(
                WarehouseLedgerEntry.warehouse_id == warehouse_id
            )
        if location_id:
            query = query.where(WarehouseLedgerEntry.location_id == location_id)
            count_query = count_query.where(
                WarehouseLedgerEntry.location_id == location_id
            )
        if project_id:
            query = query.where(WarehouseLedgerEntry.project_id == project_id)
            count_query = count_query.where(
                WarehouseLedgerEntry.project_id == project_id
            )
        if material_id:
            query = query.where(WarehouseLedgerEntry.material_id == material_id)
            count_query = count_query.where(
                WarehouseLedgerEntry.material_id == material_id
            )
        if document_type:
            query = query.where(WarehouseDocument.document_type == document_type)
            count_query = count_query.where(
                WarehouseDocument.document_type == document_type
            )
        if business_type:
            query = query.where(WarehouseDocument.business_type == business_type)
            count_query = count_query.where(
                WarehouseDocument.business_type == business_type
            )
        if category:
            query = query.where(WarehouseMaterial.category == category)
            count_query = count_query.where(WarehouseMaterial.category == category)
        if supply_type:
            query = query.where(WarehouseMaterial.supply_type == supply_type)
            count_query = count_query.where(
                WarehouseMaterial.supply_type == supply_type
            )
        if condition:
            query = query.where(WarehouseMaterial.condition == condition)
            count_query = count_query.where(WarehouseMaterial.condition == condition)
        if handler:
            like_handler = f"%{handler.strip()}%"
            query = query.where(WarehouseDocument.handler.ilike(like_handler))
            count_query = count_query.where(
                WarehouseDocument.handler.ilike(like_handler)
            )
        if q:
            like = f"%{q.strip()}%"
            query = query.where(
                WarehouseDocument.document_no.ilike(like)
                | WarehouseDocument.reference_no.ilike(like)
                | WarehouseMaterial.code.ilike(like)
                | WarehouseMaterial.name.ilike(like)
                | WarehouseLedgerEntry.batch_no.ilike(like)
                | WarehouseLedgerEntry.serial_no.ilike(like)
            )
            count_query = count_query.where(
                WarehouseDocument.document_no.ilike(like)
                | WarehouseDocument.reference_no.ilike(like)
                | WarehouseMaterial.code.ilike(like)
                | WarehouseMaterial.name.ilike(like)
                | WarehouseLedgerEntry.batch_no.ilike(like)
                | WarehouseLedgerEntry.serial_no.ilike(like)
            )
        if start_date:
            query = query.where(WarehouseLedgerEntry.occurred_on >= start_date)
            count_query = count_query.where(
                WarehouseLedgerEntry.occurred_on >= start_date
            )
        if end_date:
            query = query.where(WarehouseLedgerEntry.occurred_on <= end_date)
            count_query = count_query.where(
                WarehouseLedgerEntry.occurred_on <= end_date
            )
        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(
                WarehouseLedgerEntry.occurred_on.desc(), WarehouseLedgerEntry.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().unique().all()), int(total)

    async def list_units(self):
        result = await self.db.execute(
            select(WarehouseUnit).where(WarehouseUnit.is_active.is_(True)).order_by(WarehouseUnit.code)
        )
        return list(result.scalars().all())

    async def convert_quantity(
        self, *, from_code: str, to_code: str, quantity: Decimal
    ) -> Decimal:
        if from_code.strip().casefold() == to_code.strip().casefold():
            return quantity
        from_unit = await self._get_unit(from_code)
        to_unit = await self._get_unit(to_code)
        result = await self.db.execute(
            select(WarehouseUnitConversion).where(
                WarehouseUnitConversion.from_unit_id == from_unit.id,
                WarehouseUnitConversion.to_unit_id == to_unit.id,
            )
        )
        conversion = result.scalar_one_or_none()
        if conversion is None:
            reverse = await self.db.execute(
                select(WarehouseUnitConversion).where(
                    WarehouseUnitConversion.from_unit_id == to_unit.id,
                    WarehouseUnitConversion.to_unit_id == from_unit.id,
                )
            )
            conversion = reverse.scalar_one_or_none()
            if conversion is None:
                raise ValidationError(message=f"未配置 {from_code} 到 {to_code} 的换算")
            return (quantity / conversion.factor).quantize(Decimal("0.0001"))
        return (quantity * conversion.factor).quantize(Decimal("0.0001"))

    async def _get_unit(self, code: str) -> WarehouseUnit:
        raw = code.strip()
        result = await self.db.execute(
            select(WarehouseUnit).where(
                WarehouseUnit.is_active.is_(True),
                (WarehouseUnit.code.ilike(raw))
                | (WarehouseUnit.name == raw)
                | (WarehouseUnit.aliases.ilike(f"%{raw}%")),
            )
        )
        unit = result.scalars().first()
        if unit is None:
            raise ValidationError(message=f"未识别的计量单位: {code}")
        return unit

    async def report(self, kind: str) -> list[dict]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=False)
        today = business_today()
        if kind == "consumption":
            query = (
                select(
                    WarehouseLedgerEntry.project_id,
                    WarehouseProject.name,
                    WarehouseLedgerEntry.material_id,
                    WarehouseMaterial.code,
                    WarehouseMaterial.name,
                    WarehouseMaterial.unit,
                    func.coalesce(
                        func.sum(
                            case(
                                (WarehouseLedgerEntry.quantity_delta < 0, -WarehouseLedgerEntry.quantity_delta),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                )
                .join(WarehouseMaterial, WarehouseMaterial.id == WarehouseLedgerEntry.material_id)
                .join(WarehouseProject, WarehouseProject.id == WarehouseLedgerEntry.project_id)
                .group_by(
                    WarehouseLedgerEntry.project_id,
                    WarehouseProject.name,
                    WarehouseLedgerEntry.material_id,
                    WarehouseMaterial.code,
                    WarehouseMaterial.name,
                    WarehouseMaterial.unit,
                )
            )
            if allowed is not None:
                query = query.where(WarehouseLedgerEntry.warehouse_id.in_(allowed or [-1]))
            rows = (await self.db.execute(query)).all()
            return [
                {
                    "project_id": row[0],
                    "project_name": row[1],
                    "material_id": row[2],
                    "material_code": row[3],
                    "material_name": row[4],
                    "material_unit": row[5],
                    "outbound_qty": row[6],
                    "quantity": row[6],
                }
                for row in rows
            ]
        if kind == "turnover":
            inbound = func.coalesce(
                func.sum(case((WarehouseLedgerEntry.quantity_delta > 0, WarehouseLedgerEntry.quantity_delta), else_=0)),
                0,
            )
            outbound = func.coalesce(
                func.sum(case((WarehouseLedgerEntry.quantity_delta < 0, -WarehouseLedgerEntry.quantity_delta), else_=0)),
                0,
            )
            query = (
                select(
                    WarehouseLedgerEntry.warehouse_id,
                    Warehouse.name,
                    WarehouseLedgerEntry.material_id,
                    WarehouseMaterial.code,
                    WarehouseMaterial.name,
                    inbound.label("inbound_qty"),
                    outbound.label("outbound_qty"),
                )
                .join(Warehouse, Warehouse.id == WarehouseLedgerEntry.warehouse_id)
                .join(WarehouseMaterial, WarehouseMaterial.id == WarehouseLedgerEntry.material_id)
                .group_by(
                    WarehouseLedgerEntry.warehouse_id,
                    Warehouse.name,
                    WarehouseLedgerEntry.material_id,
                    WarehouseMaterial.code,
                    WarehouseMaterial.name,
                )
            )
            if allowed is not None:
                query = query.where(WarehouseLedgerEntry.warehouse_id.in_(allowed or [-1]))
            rows = (await self.db.execute(query)).all()
            return [
                {
                    "warehouse_id": row[0],
                    "warehouse_name": row[1],
                    "material_id": row[2],
                    "material_code": row[3],
                    "material_name": row[4],
                    "inbound_qty": row[5],
                    "outbound_qty": row[6],
                    "quantity": row[6],
                }
                for row in rows
            ]
        balances, _ = await self.list_balances(page=1, page_size=10000, include_zero=True)
        items = []
        for row in balances:
            last_moved = await self.db.execute(
                select(func.max(WarehouseLedgerEntry.occurred_on)).where(
                    WarehouseLedgerEntry.warehouse_id == row.warehouse_id,
                    WarehouseLedgerEntry.location_id == row.location_id,
                    WarehouseLedgerEntry.project_id == row.project_id,
                    WarehouseLedgerEntry.material_id == row.material_id,
                    WarehouseLedgerEntry.batch_no == (row.batch_no or ""),
                    WarehouseLedgerEntry.serial_no == (row.serial_no or ""),
                )
            )
            last_on = last_moved.scalar_one_or_none()
            idle_days = (today - last_on).days if last_on else None
            days_to_expiry = (row.expiry_date - today).days if row.expiry_date else None
            payload = {
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse.name if row.warehouse else None,
                "project_id": row.project_id,
                "project_name": row.project.name if row.project else None,
                "material_id": row.material_id,
                "material_code": row.material.code if row.material else None,
                "material_name": row.material.name if row.material else None,
                "material_unit": row.material.unit if row.material else None,
                "quantity": row.quantity,
                "minimum_stock": row.material.minimum_stock if row.material else 0,
                "last_moved_on": last_on,
                "idle_days": idle_days,
                "expiry_date": row.expiry_date,
                "days_to_expiry": days_to_expiry,
            }
            if kind == "low-stock" and row.quantity > (row.material.minimum_stock if row.material else 0):
                continue
            if kind == "idle" and (idle_days is None or idle_days < 90):
                continue
            if kind == "expiring" and (days_to_expiry is None or days_to_expiry > 30):
                continue
            if kind == "movement":
                pass
            items.append(payload)
        return items


def serialize_ledger(entry: WarehouseLedgerEntry) -> LedgerEntryResponse:
    return LedgerEntryResponse(
        id=entry.id,
        document_id=entry.document_id,
        document_no=entry.document.document_no if entry.document else None,
        document_type=entry.document.document_type if entry.document else None,
        document_line_id=entry.document_line_id,
        warehouse_id=entry.warehouse_id,
        location_id=entry.location_id,
        project_id=entry.project_id,
        material_id=entry.material_id,
        batch_no=entry.batch_no or None,
        serial_no=entry.serial_no or None,
        expiry_date=entry.expiry_date,
        quantity_delta=entry.quantity_delta,
        occurred_on=entry.occurred_on,
        business_type=entry.document.business_type if entry.document else None,
        handler=entry.document.handler if entry.document else None,
        category=entry.material.category if entry.material else None,
        supply_type=entry.material.supply_type if entry.material else None,
        condition=entry.material.condition if entry.material else None,
        created_at=entry.created_at,
        warehouse_name=entry.warehouse.name if entry.warehouse else None,
        location_name=entry.location.name if entry.location else None,
        project_name=entry.project.name if entry.project else None,
        material_code=entry.material.code if entry.material else None,
        material_name=entry.material.name if entry.material else None,
    )
