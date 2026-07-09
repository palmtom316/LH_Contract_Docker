"""Posting imported invoice allocations into formal invoice tables."""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ResourceNotFoundError, ValidationError
from app.models.contract_downstream import FinanceDownstreamInvoice
from app.models.contract_upstream import FinanceUpstreamInvoice
from app.models.invoice_import import InvoiceImportItem
from app.models.user import User


def validate_allocation_total(invoice_total: Decimal, allocation_amounts: Iterable[Decimal]) -> None:
    total = sum(allocation_amounts, Decimal("0.00"))
    if total <= Decimal("0.00"):
        raise ValidationError(message="分摊金额必须大于 0", field_errors={"amount": "分摊金额必须大于 0"})
    if total > invoice_total:
        raise ValidationError(message="分摊金额超过发票价税合计", field_errors={"amount": "分摊金额超过发票价税合计"})


class InvoicePostingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def confirm_item(self, item_id: int, user: User, override_duplicate: bool = False) -> InvoiceImportItem:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.allocations))
            .where(InvoiceImportItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ResourceNotFoundError(resource_type="导入发票", resource_id=item_id)
        if item.confirmation_status == "confirmed":
            return item
        if item.duplicate_of_item_id and not override_duplicate:
            raise ValidationError(message="重复发票不能直接确认", field_errors={"invoice_number": "请核对重复发票"})

        draft_allocations = [a for a in item.allocations if a.status == "draft"]
        validate_allocation_total(item.total_amount, [a.amount for a in draft_allocations])

        for allocation in draft_allocations:
            if allocation.direction == "upstream":
                formal = FinanceUpstreamInvoice(
                    contract_id=allocation.upstream_contract_id,
                    invoice_number=item.invoice_number,
                    invoice_date=item.invoice_date,
                    amount=allocation.amount,
                    tax_amount=allocation.tax_amount,
                    invoice_type=item.invoice_type,
                    description=allocation.description or item.remarks,
                    file_path=item.pdf_file_path or item.ofd_file_path,
                    file_key=item.pdf_file_key or item.ofd_file_key,
                    storage_provider="minio",
                    source_import_item_id=item.id,
                    source_import_allocation_id=allocation.id,
                    created_by=user.id,
                    updated_by=user.id,
                )
            else:
                formal = FinanceDownstreamInvoice(
                    contract_id=allocation.downstream_contract_id,
                    invoice_number=item.invoice_number,
                    invoice_date=item.invoice_date,
                    amount=allocation.amount,
                    tax_amount=allocation.tax_amount,
                    invoice_type=item.invoice_type,
                    supplier_name=item.seller_name,
                    description=allocation.description or item.remarks,
                    file_path=item.pdf_file_path or item.ofd_file_path,
                    file_key=item.pdf_file_key or item.ofd_file_key,
                    storage_provider="minio",
                    source_import_item_id=item.id,
                    source_import_allocation_id=allocation.id,
                    created_by=user.id,
                    updated_by=user.id,
                )
            self.db.add(formal)
            await self.db.flush()
            allocation.status = "confirmed"
            allocation.confirmed_by = user.id
            allocation.formal_invoice_id = formal.id

        item.confirmation_status = "confirmed"
        await self.db.commit()
        await self.db.refresh(item)
        return item
