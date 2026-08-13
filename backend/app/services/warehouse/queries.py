"""Warehouse query helpers and response builders."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.warehouse import (
    WarehouseDocument,
    WarehouseDocumentLine,
    WarehouseLedgerEntry,
    WarehouseMaterial,
    WarehouseStockBalance,
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
                quantity=line.quantity,
                source_warehouse_id=line.source_warehouse_id,
                source_location_id=line.source_location_id,
                source_project_id=line.source_project_id,
                target_warehouse_id=line.target_warehouse_id,
                target_location_id=line.target_location_id,
                target_project_id=line.target_project_id,
                source_warehouse_name=line.source_warehouse.name if line.source_warehouse else None,
                source_location_name=line.source_location.name if line.source_location else None,
                source_project_name=line.source_project.name if line.source_project else None,
                target_warehouse_name=line.target_warehouse.name if line.target_warehouse else None,
                target_location_name=line.target_location.name if line.target_location else None,
                target_project_name=line.target_project.name if line.target_project else None,
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
        reversed_document_id=document.reversed_document_id,
        lines=lines,
    )


def serialize_balance(row: WarehouseStockBalance) -> StockBalanceResponse:
    return StockBalanceResponse(
        warehouse_id=row.warehouse_id,
        location_id=row.location_id,
        project_id=row.project_id,
        material_id=row.material_id,
        quantity=row.quantity,
        minimum_stock=row.material.minimum_stock if row.material else Decimal("0"),
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
        warehouse_id: Optional[int] = None,
        location_id: Optional[int] = None,
        project_id: Optional[int] = None,
        material_id: Optional[int] = None,
        supply_type: Optional[str] = None,
        condition: Optional[str] = None,
        category: Optional[str] = None,
        q: Optional[str] = None,
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
            .join(WarehouseMaterial, WarehouseMaterial.id == WarehouseStockBalance.material_id)
        )
        count_query = select(func.count(WarehouseStockBalance.id)).join(
            WarehouseMaterial, WarehouseMaterial.id == WarehouseStockBalance.material_id
        )
        if allowed is not None:
            query = query.where(WarehouseStockBalance.warehouse_id.in_(allowed or [-1]))
            count_query = count_query.where(WarehouseStockBalance.warehouse_id.in_(allowed or [-1]))
        if warehouse_id:
            query = query.where(WarehouseStockBalance.warehouse_id == warehouse_id)
            count_query = count_query.where(WarehouseStockBalance.warehouse_id == warehouse_id)
        if location_id:
            query = query.where(WarehouseStockBalance.location_id == location_id)
            count_query = count_query.where(WarehouseStockBalance.location_id == location_id)
        if project_id:
            query = query.where(WarehouseStockBalance.project_id == project_id)
            count_query = count_query.where(WarehouseStockBalance.project_id == project_id)
        if material_id:
            query = query.where(WarehouseStockBalance.material_id == material_id)
            count_query = count_query.where(WarehouseStockBalance.material_id == material_id)
        if supply_type:
            query = query.where(WarehouseMaterial.supply_type == supply_type)
            count_query = count_query.where(WarehouseMaterial.supply_type == supply_type)
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
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        warehouse_id: Optional[int] = None,
        material_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WarehouseDocument], int]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=False)
        query = (
            select(WarehouseDocument)
            .options(
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.material),
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.source_warehouse),
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.source_location),
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.source_project),
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.target_warehouse),
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.target_location),
                selectinload(WarehouseDocument.lines).selectinload(WarehouseDocumentLine.target_project),
            )
            .join(WarehouseDocumentLine, WarehouseDocumentLine.document_id == WarehouseDocument.id)
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
            query.order_by(WarehouseDocument.occurred_on.desc(), WarehouseDocument.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().unique().all()), int(total)

    async def list_ledger(
        self,
        *,
        warehouse_id: Optional[int] = None,
        location_id: Optional[int] = None,
        project_id: Optional[int] = None,
        material_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[WarehouseLedgerEntry], int]:
        allowed = await self.scope.authorized_warehouse_ids(for_posting=False)
        query = select(WarehouseLedgerEntry).options(
            selectinload(WarehouseLedgerEntry.document),
            selectinload(WarehouseLedgerEntry.warehouse),
            selectinload(WarehouseLedgerEntry.location),
            selectinload(WarehouseLedgerEntry.project),
            selectinload(WarehouseLedgerEntry.material),
        )
        count_query = select(func.count(WarehouseLedgerEntry.id))
        if allowed is not None:
            query = query.where(WarehouseLedgerEntry.warehouse_id.in_(allowed or [-1]))
            count_query = count_query.where(WarehouseLedgerEntry.warehouse_id.in_(allowed or [-1]))
        if warehouse_id:
            query = query.where(WarehouseLedgerEntry.warehouse_id == warehouse_id)
            count_query = count_query.where(WarehouseLedgerEntry.warehouse_id == warehouse_id)
        if location_id:
            query = query.where(WarehouseLedgerEntry.location_id == location_id)
            count_query = count_query.where(WarehouseLedgerEntry.location_id == location_id)
        if project_id:
            query = query.where(WarehouseLedgerEntry.project_id == project_id)
            count_query = count_query.where(WarehouseLedgerEntry.project_id == project_id)
        if material_id:
            query = query.where(WarehouseLedgerEntry.material_id == material_id)
            count_query = count_query.where(WarehouseLedgerEntry.material_id == material_id)
        if start_date:
            query = query.where(WarehouseLedgerEntry.occurred_on >= start_date)
            count_query = count_query.where(WarehouseLedgerEntry.occurred_on >= start_date)
        if end_date:
            query = query.where(WarehouseLedgerEntry.occurred_on <= end_date)
            count_query = count_query.where(WarehouseLedgerEntry.occurred_on <= end_date)
        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(WarehouseLedgerEntry.occurred_on.desc(), WarehouseLedgerEntry.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().unique().all()), int(total)


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
        quantity_delta=entry.quantity_delta,
        occurred_on=entry.occurred_on,
        created_at=entry.created_at,
        warehouse_name=entry.warehouse.name if entry.warehouse else None,
        location_name=entry.location.name if entry.location else None,
        project_name=entry.project.name if entry.project else None,
        material_code=entry.material.code if entry.material else None,
        material_name=entry.material.name if entry.material else None,
    )
