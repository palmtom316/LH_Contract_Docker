"""Release 1.9 finance lifecycle integration tests against PostgreSQL."""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.bank_receipt import (
    BankReceiptAllocation,
    BankReceiptBatch,
    BankReceiptItem,
)
from app.models.invoice_import import (
    InvoiceImportAllocation,
    InvoiceImportBatch,
    InvoiceImportItem,
)
from app.models.zero_hour_labor import (
    ZeroHourLabor,
    ZeroHourLaborInvoice,
    ZeroHourLaborPayment,
)
from app.services.bank_receipt import BankReceiptService
from app.services.invoice_import.posting import InvoicePostingService
from app.services.invoice_import.service import InvoiceImportService


@pytest.mark.asyncio
async def test_bank_receipt_posts_and_clears_zero_hour_payment(test_db, test_admin):
    labor = ZeroHourLabor(
        labor_date=date(2026, 7, 1),
        attribution="COMPANY",
        total_amount=Decimal("100.00"),
        created_by=test_admin.id,
    )
    batch = BankReceiptBatch(
        batch_number="BR-INTEGRATION-1",
        original_filename="receipt.pdf",
        status="completed",
        uploaded_by=test_admin.id,
    )
    test_db.add_all([labor, batch])
    await test_db.flush()
    item = BankReceiptItem(
        batch_id=batch.id,
        source_filename="receipt.pdf",
        sha256="1" * 64,
        direction="payment",
        transaction_at=datetime(2026, 7, 2, tzinfo=timezone.utc),
        amount=Decimal("100.00"),
        status="ready",
    )
    test_db.add(item)
    await test_db.flush()
    test_db.add(
        BankReceiptAllocation(
            item_id=item.id,
            direction="payment",
            zero_hour_labor_id=labor.id,
            amount=Decimal("100.00"),
            status="draft",
        )
    )
    await test_db.commit()

    service = BankReceiptService(test_db)
    await service.confirm(item.id, test_admin)
    payment = await test_db.scalar(
        select(ZeroHourLaborPayment).where(
            ZeroHourLaborPayment.zero_hour_labor_id == labor.id
        )
    )
    assert payment.status == "active"
    assert payment.source_bank_receipt_allocation_id is not None

    await service.clear(item.id, "integration clear", test_admin)
    await test_db.refresh(payment)
    assert payment.status == "cleared"
    assert payment.amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_invoice_posts_and_clears_zero_hour_invoice(test_db, test_admin):
    labor = ZeroHourLabor(
        labor_date=date(2026, 7, 3),
        attribution="COMPANY",
        total_amount=Decimal("109.00"),
        created_by=test_admin.id,
    )
    batch = InvoiceImportBatch(
        batch_number="INV-INTEGRATION-1",
        original_filename="invoice.zip",
        status="completed",
        uploaded_by=test_admin.id,
    )
    test_db.add_all([labor, batch])
    await test_db.flush()
    item = InvoiceImportItem(
        batch_id=batch.id,
        source_archive_name="invoice.xml",
        invoice_number="INV-001",
        invoice_date=date(2026, 7, 3),
        seller_name="Supplier",
        total_amount=Decimal("109.00"),
        parse_status="parsed",
        direction="downstream",
        confirmation_status="draft",
    )
    test_db.add(item)
    await test_db.flush()
    test_db.add(
        InvoiceImportAllocation(
            item_id=item.id,
            direction="downstream",
            zero_hour_labor_id=labor.id,
            amount=Decimal("109.00"),
            tax_amount=Decimal("9.00"),
            status="draft",
            created_by=test_admin.id,
        )
    )
    await test_db.commit()

    await InvoicePostingService(test_db).confirm_item(item.id, test_admin)
    invoice = await test_db.scalar(
        select(ZeroHourLaborInvoice).where(
            ZeroHourLaborInvoice.zero_hour_labor_id == labor.id
        )
    )
    assert invoice.status == "active"
    assert invoice.source_import_allocation_id is not None

    await InvoiceImportService(test_db).clear_posting(
        item.id, "integration clear", test_admin
    )
    await test_db.refresh(invoice)
    assert invoice.status == "cleared"
    assert invoice.amount == Decimal("109.00")


@pytest.mark.asyncio
async def test_bank_receipt_job_claim_is_single_consumer(test_db, test_admin):
    test_db.add(
        BankReceiptBatch(
            batch_number="BR-JOB-1",
            original_filename="job.pdf",
            status="uploaded",
            uploaded_by=test_admin.id,
        )
    )
    await test_db.commit()
    sessions = async_sessionmaker(test_db.bind, expire_on_commit=False)
    async with sessions() as first, sessions() as second:
        claims = await asyncio.gather(
            BankReceiptService(first).claim_next_batch(),
            BankReceiptService(second).claim_next_batch(),
        )
    assert sum(claim is not None for claim in claims) == 1
