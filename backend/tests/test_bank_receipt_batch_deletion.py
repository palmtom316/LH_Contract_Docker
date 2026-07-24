from datetime import date
from decimal import Decimal

import pytest

from app.core.errors import ValidationError
from app.config import settings
from app.models.bank_receipt import (
    BankReceiptAllocation,
    BankReceiptBatch,
    BankReceiptItem,
)
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.services.bank_receipt import BankReceiptService


async def test_delete_unposted_receipt_batch_removes_source_file(
    test_db, test_admin, monkeypatch
):
    batch = BankReceiptBatch(
        batch_number="BR-DELETE-001",
        original_filename="receipt.pdf",
        status="failed",
        uploaded_by=test_admin.id,
    )
    batch.items.append(
        BankReceiptItem(
            source_filename="receipt.pdf",
            file_key="bank-receipts/receipt.pdf",
            sha256="d" * 64,
            status="failed",
        )
    )
    test_db.add(batch)
    await test_db.commit()
    await test_db.refresh(batch)

    removed = []

    class FakeMinio:
        def remove_object(self, bucket, key):
            removed.append((bucket, key))

    monkeypatch.setattr(
        "app.services.bank_receipt.get_minio_client", lambda: FakeMinio()
    )

    await BankReceiptService(test_db).delete_batch(batch.id, test_admin)

    assert await test_db.get(BankReceiptBatch, batch.id) is None
    assert removed == [
        (settings.MINIO_BUCKET_CONTRACTS, "bank-receipts/receipt.pdf")
    ]


@pytest.mark.parametrize("batch_status", ["uploaded", "processing"])
async def test_delete_active_receipt_batch_is_rejected(
    test_db, test_admin, batch_status
):
    batch = BankReceiptBatch(
        batch_number=f"BR-ACTIVE-{batch_status}",
        original_filename="receipt.pdf",
        status=batch_status,
        uploaded_by=test_admin.id,
    )
    test_db.add(batch)
    await test_db.commit()

    with pytest.raises(ValidationError, match="正在识别"):
        await BankReceiptService(test_db).delete_batch(batch.id, test_admin)


async def test_delete_posted_receipt_batch_is_rejected(test_db, test_admin):
    batch = BankReceiptBatch(
        batch_number="BR-POSTED-001",
        original_filename="receipt.pdf",
        status="completed",
        uploaded_by=test_admin.id,
    )
    item = BankReceiptItem(
        source_filename="receipt.pdf",
        sha256="p" * 64,
        direction="payment",
        amount=Decimal("100.00"),
        status="confirmed",
    )
    item.allocations.append(
        BankReceiptAllocation(
            direction="payment",
            amount=Decimal("100.00"),
            status="confirmed",
            formal_record_id=99,
        )
    )
    batch.items.append(item)
    test_db.add(batch)
    await test_db.commit()

    with pytest.raises(ValidationError, match="已入账"):
        await BankReceiptService(test_db).delete_batch(batch.id, test_admin)

    assert await test_db.get(BankReceiptBatch, batch.id) is not None


async def test_clear_receipt_batch_only_clears_current_posting(test_db, test_admin):
    contract = ContractUpstream(
        serial_number=9303,
        contract_code="UP-RECEIPT-CLEAR",
        contract_name="回单批次清除合同",
        party_a_name="甲方",
        party_b_name="乙方",
        contract_amount=Decimal("1000.00"),
    )
    batch = BankReceiptBatch(
        batch_number="BR-CLEAR-BATCH",
        original_filename="receipt.pdf",
        status="completed",
        uploaded_by=test_admin.id,
    )
    item = BankReceiptItem(
        source_filename="receipt.pdf",
        sha256="c" * 64,
        direction="receipt",
        amount=Decimal("100.00"),
        status="confirmed",
    )
    batch.items.append(item)
    test_db.add_all([contract, batch])
    await test_db.flush()
    old_allocation = BankReceiptAllocation(
        item_id=item.id,
        direction="receipt",
        upstream_contract_id=contract.id,
        amount=Decimal("80.00"),
        status="cleared",
        formal_record_id=999,
    )
    current_allocation = BankReceiptAllocation(
        item_id=item.id,
        direction="receipt",
        upstream_contract_id=contract.id,
        amount=Decimal("100.00"),
        status="confirmed",
    )
    test_db.add_all([old_allocation, current_allocation])
    await test_db.flush()
    formal = FinanceUpstreamReceipt(
        contract_id=contract.id,
        receipt_date=date(2026, 7, 24),
        amount=Decimal("100.00"),
        source_bank_receipt_item_id=item.id,
        source_bank_receipt_allocation_id=current_allocation.id,
        created_by=test_admin.id,
    )
    test_db.add(formal)
    await test_db.flush()
    current_allocation.formal_record_id = formal.id
    await test_db.commit()

    result = await BankReceiptService(test_db).clear_batch(
        batch.id, "批次冲销", test_admin
    )

    await test_db.refresh(item)
    await test_db.refresh(old_allocation)
    await test_db.refresh(formal)
    assert item.status == "cleared"
    assert old_allocation.status == "cleared"
    assert old_allocation.formal_record_id == 999
    assert formal.posting_status == "cleared"
    assert formal.original_amount == Decimal("100.00")
    assert formal.amount == Decimal("0.00")
    assert result.confirmed_items == 0
    assert result.posted_items == 1
