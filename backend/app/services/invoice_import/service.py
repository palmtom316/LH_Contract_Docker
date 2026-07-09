"""Batch-level invoice import service operations."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import tempfile
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.errors import ResourceNotFoundError, ValidationError
from app.core.minio import ensure_bucket_exists, get_minio_client
from app.models.invoice_import import InvoiceImportAllocation, InvoiceImportBatch, InvoiceImportItem
from app.models.user import User
from app.schemas.invoice_import import AllocationCreate, AllocationUpdate
from app.services.invoice_import.archive import UnsafeArchiveError, extract_invoice_archives
from app.services.invoice_import.matching import InvoiceMatchService, build_dedupe_key, detect_direction
from app.services.invoice_import.parser import parse_invoice_xml


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

    async def create_batch_from_upload(self, file: UploadFile, user: User) -> InvoiceImportBatch:
        filename = file.filename or ""
        if not filename.lower().endswith(".zip"):
            raise ValidationError(message="文件格式错误", field_errors={"file": "只支持 zip 压缩包"})
        content = await file.read()
        if len(content) > settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE:
            raise ValidationError(message="文件过大", field_errors={"file": "发票批次压缩包超过大小限制"})

        object_key = f"invoices/imports/batches/{datetime.utcnow().strftime('%Y/%m')}/{uuid.uuid4()}.zip"
        batch = InvoiceImportBatch(
            batch_number=f"INVIMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            original_filename=filename,
            archive_file_path=object_key,
            archive_file_key=object_key,
            status="uploaded",
            uploaded_by=user.id,
        )
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        await self._put_bytes_to_minio(batch.archive_file_key, content, "application/zip")
        return batch

    async def process_uploaded_batch(self, batch_id: int) -> None:
        batch = await self.get_batch(batch_id)
        content = await self._get_bytes_from_minio(batch.archive_file_key)
        parsed_count = 0
        failed_count = 0
        duplicate_count = 0
        total_count = 0

        batch.status = "processing"
        await self.db.commit()

        with tempfile.TemporaryDirectory(prefix="invoice-import-") as tmp:
            work_dir = Path(tmp)
            try:
                packages = extract_invoice_archives(BytesIO(content), work_dir)
            except UnsafeArchiveError as exc:
                batch.status = "failed"
                batch.failed_items = 1
                await self.db.commit()
                raise ValidationError(message="发票压缩包不安全或格式错误", field_errors={"file": str(exc)}) from exc

            total_count = len(packages)
            for package in packages:
                try:
                    parsed = parse_invoice_xml(package.xml_path.read_bytes())
                    dedupe_key = build_dedupe_key(parsed)
                    direction = detect_direction(parsed, settings.COMPANY_TAX_NO)
                    duplicate = await self._find_duplicate(dedupe_key)
                    item = InvoiceImportItem(
                        batch_id=batch.id,
                        source_archive_name=package.source_archive_name,
                        invoice_number=parsed.invoice_number,
                        invoice_code=parsed.invoice_code,
                        invoice_date=parsed.invoice_date,
                        seller_name=parsed.seller_name,
                        seller_tax_no=parsed.seller_tax_no,
                        buyer_name=parsed.buyer_name,
                        buyer_tax_no=parsed.buyer_tax_no,
                        amount_without_tax=parsed.amount_without_tax,
                        tax_amount=parsed.tax_amount,
                        total_amount=parsed.total_amount,
                        invoice_type=parsed.invoice_type,
                        remarks=parsed.remarks,
                        dedupe_key=dedupe_key,
                        duplicate_of_item_id=duplicate.id if duplicate else None,
                        direction=direction,
                        parse_status="parsed",
                        match_status="not_matched",
                        confirmation_status="draft",
                        pdf_file_path=str(package.pdf_path) if package.pdf_path else None,
                        ofd_file_path=str(package.ofd_path) if package.ofd_path else None,
                        xml_file_path=str(package.xml_path),
                        raw_xml=package.xml_path.read_text(encoding="utf-8", errors="ignore"),
                        parsed_payload=parsed.payload,
                    )
                    self.db.add(item)
                    await self.db.flush()
                    if duplicate:
                        duplicate_count += 1
                    candidates = await InvoiceMatchService(self.db).find_candidates(item)
                    item.match_status = "matched" if candidates else "not_matched"
                    for candidate in candidates:
                        self.db.add(candidate)
                    parsed_count += 1
                except Exception as exc:  # item-level parse/import failure
                    failed_count += 1
                    self.db.add(InvoiceImportItem(
                        batch_id=batch.id,
                        source_archive_name=package.source_archive_name,
                        direction="unknown",
                        parse_status="failed",
                        match_status="not_matched",
                        confirmation_status="draft",
                        error_code=type(exc).__name__,
                        error_message=str(exc),
                    ))
            batch.total_items = total_count
            batch.parsed_items = parsed_count
            batch.failed_items = failed_count
            batch.duplicate_items = duplicate_count
            batch.status = "completed_with_errors" if failed_count else "completed"
            batch.processed_at = datetime.utcnow()
            await self.db.commit()

    async def _find_duplicate(self, dedupe_key: str) -> InvoiceImportItem | None:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .where(InvoiceImportItem.dedupe_key == dedupe_key, InvoiceImportItem.duplicate_of_item_id.is_(None))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _put_bytes_to_minio(self, object_key: str, content: bytes, content_type: str) -> None:
        client = get_minio_client()
        bucket_name = settings.MINIO_BUCKET_CONTRACTS
        ensure_bucket_exists(client, bucket_name)
        client.put_object(bucket_name, object_key, BytesIO(content), length=len(content), content_type=content_type)

    async def _get_bytes_from_minio(self, object_key: str) -> bytes:
        client = get_minio_client()
        response = client.get_object(settings.MINIO_BUCKET_CONTRACTS, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
