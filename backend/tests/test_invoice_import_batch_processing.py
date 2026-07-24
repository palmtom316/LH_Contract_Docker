from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi import UploadFile
from sqlalchemy import func, select

from app.core.errors import ValidationError
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamInvoice
from app.models.invoice_import import (
    InvoiceImportAllocation,
    InvoiceImportBatch,
    InvoiceImportItem,
    InvoiceImportMatchCandidate,
)
from app.schemas.invoice_import import ImportItemResponse
from app.services.invoice_import.service import InvoiceImportService
from app.services.invoice_import.matching import build_dedupe_key
from app.services.invoice_import.parser import ParsedInvoice


def test_import_dedupe_key_for_realistic_invoice():
    parsed = ParsedInvoice(
        invoice_number="24572000000000123456",
        invoice_code=None,
        invoice_date=date(2026, 7, 8),
        seller_name="我方公司",
        seller_tax_no="913000000000000001",
        buyer_name="客户A",
        buyer_tax_no="913000000000000002",
        amount_without_tax=Decimal("1000.00"),
        tax_rate=Decimal("6.00"),
        tax_amount=Decimal("60.00"),
        total_amount=Decimal("1060.00"),
        invoice_type="电子发票",
        remarks="项目合同 HT-2026-001",
        project_name="项目名称",
        construction_project_name="建筑项目名称",
        payload={},
    )

    assert build_dedupe_key(parsed) == "24572000000000123456|913000000000000001|913000000000000002|2026-07-08|1060.00"


async def test_same_second_uploads_use_distinct_batch_numbers(test_db, test_admin, monkeypatch):
    async def fake_put(*_args, **_kwargs):
        return None

    service = InvoiceImportService(test_db)
    monkeypatch.setattr(service, "_put_bytes_to_minio", fake_put)
    first = await service.create_batch_from_upload(UploadFile(filename="first.zip", file=BytesIO(b"first")), test_admin)
    second = await service.create_batch_from_upload(UploadFile(filename="second.zip", file=BytesIO(b"second")), test_admin)

    assert first.batch_number != second.batch_number


async def test_minio_failure_does_not_create_batch(test_db, test_admin, monkeypatch):
    async def fail_put(*_args, **_kwargs):
        raise RuntimeError("minio unavailable")

    service = InvoiceImportService(test_db)
    monkeypatch.setattr(service, "_put_bytes_to_minio", fail_put)

    with pytest.raises(RuntimeError, match="minio unavailable"):
        await service.create_batch_from_upload(UploadFile(filename="failed.zip", file=BytesIO(b"failed")), test_admin)

    count = await test_db.scalar(select(func.count(InvoiceImportBatch.id)))
    assert count == 0


async def test_delete_unconfirmed_import_batch(test_db, test_admin, monkeypatch):
    batch = InvoiceImportBatch(
        batch_number="INVIMP-DELETE-001",
        original_filename="failed.zip",
        archive_file_key="invoices/imports/batches/failed.zip",
        status="failed",
        uploaded_by=test_admin.id,
    )
    test_db.add(batch)
    await test_db.commit()
    await test_db.refresh(batch)
    removed = []
    service = InvoiceImportService(test_db)
    monkeypatch.setattr(service, "_remove_minio_object", removed.append)

    await service.delete_batch(batch.id, test_admin)

    assert await test_db.get(InvoiceImportBatch, batch.id) is None
    assert removed == ["invoices/imports/batches/failed.zip"]


async def test_delete_confirmed_import_batch_is_rejected(test_db, test_admin):
    batch = InvoiceImportBatch(
        batch_number="INVIMP-CONFIRMED-001",
        original_filename="confirmed.zip",
        status="completed",
        uploaded_by=test_admin.id,
    )
    batch.items.append(InvoiceImportItem(
        source_archive_name="invoice.zip",
        direction="upstream",
        confirmation_status="confirmed",
    ))
    test_db.add(batch)
    await test_db.commit()

    with pytest.raises(ValidationError, match="已确认挂账"):
        await InvoiceImportService(test_db).delete_batch(batch.id, test_admin)

    assert await test_db.get(InvoiceImportBatch, batch.id) is not None


async def test_clear_import_batch_preserves_posting_history(test_db, test_admin):
    contract = ContractUpstream(
        serial_number=9302,
        contract_code="UP-CLEAR-BATCH",
        contract_name="批次清除合同",
        party_a_name="甲方",
        party_b_name="乙方",
        contract_amount=Decimal("1000.00"),
    )
    batch = InvoiceImportBatch(
        batch_number="INVIMP-CLEAR-BATCH",
        original_filename="clear.zip",
        status="completed",
        uploaded_by=test_admin.id,
    )
    test_db.add_all([contract, batch])
    await test_db.flush()
    item = InvoiceImportItem(
        batch_id=batch.id,
        source_archive_name="invoice.zip",
        confirmation_status="confirmed",
        direction="upstream",
        parse_status="parsed",
    )
    test_db.add(item)
    await test_db.flush()
    allocation = InvoiceImportAllocation(
        item_id=item.id,
        direction="upstream",
        upstream_contract_id=contract.id,
        amount=Decimal("100.00"),
        status="confirmed",
        created_by=test_admin.id,
    )
    test_db.add(allocation)
    await test_db.flush()
    formal = FinanceUpstreamInvoice(
        contract_id=contract.id,
        invoice_date=date(2026, 7, 24),
        amount=Decimal("100.00"),
        source_import_item_id=item.id,
        source_import_allocation_id=allocation.id,
        created_by=test_admin.id,
    )
    test_db.add(formal)
    await test_db.flush()
    allocation.formal_invoice_id = formal.id
    await test_db.commit()

    result = await InvoiceImportService(test_db).clear_batch(
        batch.id, "批次冲销", test_admin
    )

    await test_db.refresh(item)
    await test_db.refresh(formal)
    assert item.confirmation_status == "cleared"
    assert formal.posting_status == "cleared"
    assert formal.original_amount == Decimal("100.00")
    assert formal.amount == Decimal("0.00")
    assert result.confirmed_items == 0
    assert result.posted_items == 1
    with pytest.raises(ValidationError, match="已确认挂账"):
        await InvoiceImportService(test_db).delete_batch(batch.id, test_admin)


async def test_list_items_includes_matched_contract_identity(test_db, test_admin):
    contract = ContractUpstream(
        serial_number=9301,
        contract_code="UP-CARD-001",
        contract_name="建筑项目匹配合同",
        party_a_name="甲方",
        party_b_name="乙方",
        contract_amount=Decimal("1000.00"),
    )
    batch = InvoiceImportBatch(
        batch_number="INVIMP-CARD-001",
        original_filename="card.zip",
        status="completed",
        uploaded_by=test_admin.id,
    )
    test_db.add_all([contract, batch])
    await test_db.flush()
    item = InvoiceImportItem(
        batch_id=batch.id,
        source_archive_name="invoice.zip",
        invoice_number="CARD-001",
        direction="upstream",
        parse_status="parsed",
        match_status="matched",
        confirmation_status="draft",
        project_name="项目名称",
        construction_project_name="建筑项目名称",
    )
    test_db.add(item)
    await test_db.flush()
    test_db.add(InvoiceImportMatchCandidate(
        item_id=item.id,
        direction="upstream",
        upstream_contract_id=contract.id,
        score=100,
        matched_signals={"construction_project_name": 100},
    ))
    await test_db.commit()

    listed = await InvoiceImportService(test_db).list_items(batch.id, test_admin)
    response = ImportItemResponse.model_validate(listed[0])

    assert response.project_name == "项目名称"
    assert response.construction_project_name == "建筑项目名称"
    assert response.candidates[0].contract_serial_number == 9301
    assert response.candidates[0].contract_code == "UP-CARD-001"
    assert response.candidates[0].contract_name == "建筑项目匹配合同"
