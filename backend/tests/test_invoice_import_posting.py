from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.core.errors import ValidationError
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamInvoice
from app.models.invoice_import import InvoiceImportAllocation, InvoiceImportBatch, InvoiceImportItem
from app.services.invoice_import.posting import InvoicePostingService, validate_allocation_total


def test_rejects_allocation_total_above_invoice_total():
    with pytest.raises(ValidationError):
        validate_allocation_total(Decimal("100.00"), [Decimal("60.00"), Decimal("50.00")])


def test_accepts_allocation_total_equal_invoice_total():
    validate_allocation_total(Decimal("100.00"), [Decimal("60.00"), Decimal("40.00")])


def test_rejects_missing_invoice_total_with_validation_error():
    with pytest.raises(ValidationError):
        validate_allocation_total(None, [Decimal("1.00")])


async def test_confirm_rejects_item_without_allocations(test_db, test_admin):
    batch = InvoiceImportBatch(
        batch_number="INVIMP-EMPTY",
        original_filename="empty.zip",
        status="completed",
        uploaded_by=test_admin.id,
    )
    test_db.add(batch)
    await test_db.flush()
    item = InvoiceImportItem(
        batch_id=batch.id,
        source_archive_name="invoice.zip",
        invoice_number="EMPTY-001",
        invoice_date=date(2026, 7, 16),
        total_amount=Decimal("100.00"),
        tax_rate=Decimal("9.00"),
        direction="upstream",
        parse_status="parsed",
        match_status="not_matched",
        confirmation_status="draft",
    )
    test_db.add(item)
    await test_db.commit()

    with pytest.raises(ValidationError, match="尚未分摊"):
        await InvoicePostingService(test_db).confirm_item(item.id, test_admin)


async def test_repeated_confirmation_is_idempotent(test_db, test_admin):
    contract = ContractUpstream(
        serial_number=8100,
        contract_code="UP-IDEMPOTENT",
        contract_name="幂等确认合同",
        party_a_name="甲方",
        party_b_name="乙方",
        contract_amount=Decimal("1000.00"),
    )
    batch = InvoiceImportBatch(
        batch_number="INVIMP-IDEMPOTENT",
        original_filename="idempotent.zip",
        status="completed",
        uploaded_by=test_admin.id,
    )
    test_db.add_all([contract, batch])
    await test_db.flush()
    item = InvoiceImportItem(
        batch_id=batch.id,
        source_archive_name="invoice.zip",
        invoice_number="IDEMPOTENT-001",
        invoice_date=date(2026, 7, 16),
        total_amount=Decimal("100.00"),
        tax_rate=Decimal("9.00"),
        direction="upstream",
        parse_status="parsed",
        match_status="matched",
        confirmation_status="draft",
        pdf_file_path="invoices/imports/items/INVIMP-IDEMPOTENT/invoice.pdf",
        pdf_file_key="invoices/imports/items/INVIMP-IDEMPOTENT/invoice.pdf",
        xml_file_path="invoices/imports/items/INVIMP-IDEMPOTENT/invoice.xml",
        xml_file_key="invoices/imports/items/INVIMP-IDEMPOTENT/invoice.xml",
    )
    test_db.add(item)
    await test_db.flush()
    test_db.add(InvoiceImportAllocation(
        item_id=item.id,
        direction="upstream",
        upstream_contract_id=contract.id,
        amount=Decimal("100.00"),
        status="draft",
        created_by=test_admin.id,
    ))
    await test_db.commit()

    service = InvoicePostingService(test_db)
    await service.confirm_item(item.id, test_admin)
    await service.confirm_item(item.id, test_admin)

    count = await test_db.scalar(select(func.count(FinanceUpstreamInvoice.id)))
    assert count == 1
    formal_invoice = await test_db.scalar(select(FinanceUpstreamInvoice))
    assert formal_invoice.file_path == "invoices/imports/items/INVIMP-IDEMPOTENT/invoice.pdf"
    assert formal_invoice.file_key == "invoices/imports/items/INVIMP-IDEMPOTENT/invoice.pdf"
    assert formal_invoice.storage_provider == "minio"
    assert formal_invoice.tax_rate == Decimal("9.00")
