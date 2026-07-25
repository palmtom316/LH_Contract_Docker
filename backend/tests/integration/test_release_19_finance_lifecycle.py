"""Release 1.9 finance lifecycle integration tests against PostgreSQL."""

import asyncio
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.invoice_import import (
    InvoiceImportAllocation,
    InvoiceImportBatch,
    InvoiceImportItem,
)
from app.models.zero_hour_labor import (
    ZeroHourLabor,
    ZeroHourLaborInvoice,
)
from app.services.invoice_import.posting import InvoicePostingService
from app.services.invoice_import.service import InvoiceImportService


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
async def test_invoice_import_job_claim_is_single_consumer(test_db, test_admin):
    test_db.add(
        InvoiceImportBatch(
            batch_number="INV-JOB-1",
            original_filename="job.zip",
            status="uploaded",
            uploaded_by=test_admin.id,
        )
    )
    await test_db.commit()
    sessions = async_sessionmaker(test_db.bind, expire_on_commit=False)
    async with sessions() as first, sessions() as second:
        claims = await asyncio.gather(
            InvoiceImportService(first).claim_next_batch(),
            InvoiceImportService(second).claim_next_batch(),
        )
    assert sum(claim is not None for claim in claims) == 1
