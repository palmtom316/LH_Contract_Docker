"""Posting imported invoice allocations into formal invoice tables."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ResourceNotFoundError, ValidationError
from app.models.contract_downstream import FinanceDownstreamInvoice
from app.models.contract_upstream import FinanceUpstreamInvoice
from app.models.invoice_import import InvoiceImportAllocation, InvoiceImportItem
from app.models.user import User, UserRole


def validate_allocation_total(invoice_total: Decimal | None, allocation_amounts: Iterable[Decimal]) -> None:
    total = sum((amount or Decimal("0.00") for amount in allocation_amounts), Decimal("0.00"))
    if total <= Decimal("0.00"):
        raise ValidationError(message="分摊金额必须大于 0", field_errors={"amount": "分摊金额必须大于 0"})
    if invoice_total is None:
        raise ValidationError(message="发票价税合计缺失，不能确认", field_errors={"total_amount": "发票价税合计缺失"})
    if total > invoice_total:
        raise ValidationError(message="分摊金额超过发票价税合计", field_errors={"amount": "分摊金额超过发票价税合计"})


def _can_access_imports(user: User) -> bool:
    return bool(getattr(user, "is_superuser", False) or getattr(user, "role", None) in {
        UserRole.ADMIN,
    })


def _invoice_file_fields(item: InvoiceImportItem) -> tuple[str | None, str | None]:
    file_key = item.pdf_file_key or item.ofd_file_key or item.xml_file_key
    file_path = item.pdf_file_path or item.ofd_file_path or item.xml_file_path
    if file_key:
        return file_key, file_key
    return file_path, None


def _validate_item_before_posting(item: InvoiceImportItem) -> None:
    errors: dict[str, str] = {}
    if item.invoice_date is None:
        errors["invoice_date"] = "开票日期缺失"
    if not item.invoice_number:
        errors["invoice_number"] = "发票号码缺失"
    if item.parse_status != "parsed":
        errors["parse_status"] = "只有解析成功的发票可以确认"
    if errors:
        raise ValidationError(message="发票关键信息不完整，不能确认", field_errors=errors)


def _validate_allocation(allocation: InvoiceImportAllocation) -> None:
    if allocation.direction == "upstream":
        if not allocation.upstream_contract_id or allocation.downstream_contract_id:
            raise ValidationError(message="上游分摊必须且只能选择上游合同", field_errors={"upstream_contract_id": "请选择上游合同"})
        return
    if allocation.direction == "downstream":
        if not allocation.downstream_contract_id or allocation.upstream_contract_id:
            raise ValidationError(message="下游分摊必须且只能选择下游合同", field_errors={"downstream_contract_id": "请选择下游合同"})
        return
    raise ValidationError(message="分摊方向必须为上游或下游", field_errors={"direction": "分摊方向无效"})


class InvoicePostingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def confirm_item(self, item_id: int, user: User, override_duplicate: bool = False) -> InvoiceImportItem:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.allocations), selectinload(InvoiceImportItem.candidates), selectinload(InvoiceImportItem.batch))
            .where(InvoiceImportItem.id == item_id)
            .with_for_update()
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ResourceNotFoundError(resource_type="导入发票", resource_id=item_id)
        if not _can_access_imports(user) and item.batch and item.batch.uploaded_by != user.id:
            raise ResourceNotFoundError(resource_type="导入发票", resource_id=item_id)
        if item.duplicate_of_item_id and not override_duplicate:
            raise ValidationError(message="重复发票不能直接确认", field_errors={"invoice_number": "请核对重复发票"})

        if item.confirmation_status == "confirmed":
            return item

        draft_allocations = [a for a in item.allocations if a.status == "draft"]
        if not draft_allocations:
            raise ValidationError(message="发票尚未分摊，不能确认挂账", field_errors={"allocations": "请先添加分摊记录"})

        _validate_item_before_posting(item)
        for allocation in draft_allocations:
            _validate_allocation(allocation)
        validate_allocation_total(item.total_amount, [a.amount for a in item.allocations if a.status in {"draft", "confirmed"}])

        file_path, file_key = _invoice_file_fields(item)
        now = datetime.utcnow()
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
                    file_path=file_path,
                    file_key=file_key,
                    storage_provider="minio" if file_key else "local",
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
                    file_path=file_path,
                    file_key=file_key,
                    storage_provider="minio" if file_key else "local",
                    source_import_item_id=item.id,
                    source_import_allocation_id=allocation.id,
                    created_by=user.id,
                    updated_by=user.id,
                )
            self.db.add(formal)
            await self.db.flush()
            allocation.status = "confirmed"
            allocation.confirmed_by = user.id
            allocation.confirmed_at = now
            allocation.formal_invoice_id = formal.id

        item.confirmation_status = "confirmed"
        await self.db.commit()
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.allocations), selectinload(InvoiceImportItem.candidates), selectinload(InvoiceImportItem.batch))
            .where(InvoiceImportItem.id == item_id)
        )
        return result.scalar_one()
