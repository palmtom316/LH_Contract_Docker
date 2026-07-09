"""Batch-level invoice import service operations."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ResourceNotFoundError
from app.models.invoice_import import InvoiceImportAllocation, InvoiceImportBatch, InvoiceImportItem
from app.models.user import User
from app.schemas.invoice_import import AllocationCreate, AllocationUpdate


class InvoiceImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_batches(self) -> list[InvoiceImportBatch]:
        result = await self.db.execute(select(InvoiceImportBatch).order_by(InvoiceImportBatch.created_at.desc()))
        return list(result.scalars().all())

    async def get_batch(self, batch_id: int) -> InvoiceImportBatch:
        result = await self.db.execute(select(InvoiceImportBatch).where(InvoiceImportBatch.id == batch_id))
        batch = result.scalar_one_or_none()
        if not batch:
            raise ResourceNotFoundError(resource_type="发票导入批次", resource_id=batch_id)
        return batch

    async def list_items(self, batch_id: int) -> list[InvoiceImportItem]:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.allocations), selectinload(InvoiceImportItem.candidates))
            .where(InvoiceImportItem.batch_id == batch_id)
            .order_by(InvoiceImportItem.id.desc())
        )
        return list(result.scalars().all())

    async def create_allocation(self, item_id: int, allocation_in: AllocationCreate, user: User) -> InvoiceImportAllocation:
        data = allocation_in.model_dump()
        allocation = InvoiceImportAllocation(item_id=item_id, created_by=user.id, **data)
        self.db.add(allocation)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation

    async def update_allocation(self, allocation_id: int, allocation_in: AllocationUpdate) -> InvoiceImportAllocation:
        result = await self.db.execute(select(InvoiceImportAllocation).where(InvoiceImportAllocation.id == allocation_id))
        allocation = result.scalar_one_or_none()
        if not allocation:
            raise ResourceNotFoundError(resource_type="发票分摊", resource_id=allocation_id)
        for key, value in allocation_in.model_dump(exclude_unset=True).items():
            setattr(allocation, key, value)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation
