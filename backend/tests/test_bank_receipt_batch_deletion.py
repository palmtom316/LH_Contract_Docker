from decimal import Decimal

import pytest

from app.core.errors import ValidationError
from app.config import settings
from app.models.bank_receipt import (
    BankReceiptAllocation,
    BankReceiptBatch,
    BankReceiptItem,
)
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
