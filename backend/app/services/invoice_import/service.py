"""Batch-level invoice import service operations."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import tempfile
import uuid

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.errors import ResourceNotFoundError, ValidationError
from app.core.minio import ensure_bucket_exists, get_minio_client
from app.models.invoice_import import (
    InvoiceImportAllocation,
    InvoiceImportBatch,
    InvoiceImportItem,
    InvoiceImportMatchCandidate,
)
from app.models.user import User, UserRole
from app.schemas.invoice_import import AllocationCreate, AllocationUpdate, InvoiceDirection
from app.models.contract_upstream import FinanceUpstreamInvoice
from app.models.contract_downstream import FinanceDownstreamInvoice
from app.models.contract_management import FinanceManagementInvoice
from app.services.audit_service import create_audit_log
from app.services.invoice_import.archive import ExtractedInvoicePackage, UnsafeArchiveError, extract_invoice_archives
from app.services.invoice_import.matching import InvoiceMatchService, build_dedupe_key, detect_direction
from app.services.invoice_import.parser import parse_invoice_xml


_CHUNK_SIZE = 1024 * 1024


def _can_access_all_imports(user: User | None) -> bool:
    if user is None:
        return True
    return bool(getattr(user, "is_superuser", False) or getattr(user, "role", None) in {
        UserRole.ADMIN,
    })


def _apply_confirmed_count(batch: InvoiceImportBatch, confirmed_count: int | None) -> InvoiceImportBatch:
    batch._confirmed_items_count = int(confirmed_count or 0)
    return batch


class InvoiceImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_batches(self, current_user: User | None = None) -> list[InvoiceImportBatch]:
        confirmed_count = (
            select(func.count(InvoiceImportItem.id))
            .where(
                InvoiceImportItem.batch_id == InvoiceImportBatch.id,
                InvoiceImportItem.confirmation_status == "confirmed",
            )
            .correlate(InvoiceImportBatch)
            .scalar_subquery()
        )
        query = select(InvoiceImportBatch, confirmed_count.label("confirmed_count"))
        if current_user and not _can_access_all_imports(current_user):
            query = query.where(InvoiceImportBatch.uploaded_by == current_user.id)
        query = query.order_by(InvoiceImportBatch.created_at.desc())
        result = await self.db.execute(query)
        return [_apply_confirmed_count(batch, count) for batch, count in result.all()]

    async def get_batch(self, batch_id: int, current_user: User | None = None) -> InvoiceImportBatch:
        confirmed_count = (
            select(func.count(InvoiceImportItem.id))
            .where(
                InvoiceImportItem.batch_id == InvoiceImportBatch.id,
                InvoiceImportItem.confirmation_status == "confirmed",
            )
            .correlate(InvoiceImportBatch)
            .scalar_subquery()
        )
        query = select(InvoiceImportBatch, confirmed_count.label("confirmed_count")).where(InvoiceImportBatch.id == batch_id)
        if current_user and not _can_access_all_imports(current_user):
            query = query.where(InvoiceImportBatch.uploaded_by == current_user.id)
        result = await self.db.execute(query)
        row = result.one_or_none()
        if not row:
            raise ResourceNotFoundError(resource_type="发票导入批次", resource_id=batch_id)
        batch, count = row
        return _apply_confirmed_count(batch, count)

    async def list_items(self, batch_id: int, current_user: User | None = None) -> list[InvoiceImportItem]:
        candidate_contracts = selectinload(InvoiceImportItem.candidates)
        query = (
            select(InvoiceImportItem)
            .join(InvoiceImportItem.batch)
            .options(
                selectinload(InvoiceImportItem.allocations),
                candidate_contracts.selectinload(InvoiceImportMatchCandidate.upstream_contract),
                candidate_contracts.selectinload(InvoiceImportMatchCandidate.downstream_contract),
            )
            .where(InvoiceImportItem.batch_id == batch_id)
        )
        if current_user and not _can_access_all_imports(current_user):
            query = query.where(InvoiceImportBatch.uploaded_by == current_user.id)
        query = query.order_by(InvoiceImportItem.id.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_batch(self, batch_id: int, current_user: User) -> None:
        query = (
            select(InvoiceImportBatch)
            .options(
                selectinload(InvoiceImportBatch.items).selectinload(InvoiceImportItem.allocations),
                selectinload(InvoiceImportBatch.items).selectinload(InvoiceImportItem.candidates),
            )
            .where(InvoiceImportBatch.id == batch_id)
        )
        if not _can_access_all_imports(current_user):
            query = query.where(InvoiceImportBatch.uploaded_by == current_user.id)
        result = await self.db.execute(query)
        batch = result.scalar_one_or_none()
        if not batch:
            raise ResourceNotFoundError(resource_type="发票导入批次", resource_id=batch_id)
        if batch.status in {"uploaded", "processing"}:
            raise ValidationError(
                message="正在解析的导入批次不能删除",
                field_errors={"batch": "请等待解析完成后重试"},
            )
        if any(
            item.confirmation_status == "confirmed"
            or any(allocation.status == "confirmed" or allocation.formal_invoice_id for allocation in item.allocations)
            for item in batch.items
        ):
            raise ValidationError(
                message="已确认挂账的导入批次不能删除",
                field_errors={"batch": "请先在对应合同中处理已生成的挂账记录"},
            )

        object_keys = {
            key
            for key in [
                batch.archive_file_key,
                *(item.pdf_file_key for item in batch.items),
                *(item.ofd_file_key for item in batch.items),
                *(item.xml_file_key for item in batch.items),
            ]
            if key
        }
        await self.db.delete(batch)
        await self.db.commit()
        for object_key in object_keys:
            self._remove_minio_object(object_key)

    async def create_allocation(self, item_id: int, allocation_in: AllocationCreate, user: User) -> InvoiceImportAllocation:
        item = await self._get_item_for_user(item_id, user)
        if item.confirmation_status not in {"draft", "cleared"}:
            raise ValidationError(message="当前状态不能修改分摊")
        data = allocation_in.model_dump()
        allocation = InvoiceImportAllocation(item_id=item.id, created_by=user.id, **data)
        self.db.add(allocation)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation

    async def update_allocation(self, allocation_id: int, allocation_in: AllocationUpdate, user: User) -> InvoiceImportAllocation:
        result = await self.db.execute(
            select(InvoiceImportAllocation)
            .options(selectinload(InvoiceImportAllocation.item).selectinload(InvoiceImportItem.batch))
            .where(InvoiceImportAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        if not allocation or (not _can_access_all_imports(user) and allocation.item.batch.uploaded_by != user.id):
            raise ResourceNotFoundError(resource_type="发票分摊", resource_id=allocation_id)
        if allocation.status != "draft":
            raise ValidationError(message="只能修改草稿分摊", field_errors={"status": "只能修改草稿分摊"})

        update_data = allocation_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(allocation, key, value)
        self._validate_allocation_target(allocation.direction, allocation.upstream_contract_id, allocation.downstream_contract_id, allocation.management_contract_id)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation

    async def ignore_item(self, item_id: int, reason: str, user: User) -> InvoiceImportItem:
        item = await self._get_item_for_user(item_id, user)
        if item.confirmation_status != "draft" or item.parse_status in {"processing", "failed"}:
            raise ValidationError(message="当前状态不能忽略")
        item.confirmation_status = "ignored"; item.ignored_reason = reason; item.ignored_by = user.id; item.ignored_at = datetime.utcnow()
        await create_audit_log(self.db, user, "UPDATE", "发票导入", item.id, description=reason, new_values={"status":"ignored"})
        await self.db.commit(); return item

    async def clear_posting(self, item_id: int, reason: str, user: User) -> InvoiceImportItem:
        result = await self.db.execute(select(InvoiceImportItem).options(selectinload(InvoiceImportItem.allocations),selectinload(InvoiceImportItem.batch)).where(InvoiceImportItem.id==item_id).with_for_update())
        item=result.scalar_one_or_none()
        if not item: raise ResourceNotFoundError(resource_type="导入发票",resource_id=item_id)
        if item.confirmation_status == "cleared": return item
        if item.confirmation_status != "confirmed": raise ValidationError(message="只有已挂账发票可以清除挂账")
        snapshot=[]
        for allocation in item.allocations:
            if allocation.status != "confirmed": continue
            table=FinanceUpstreamInvoice if allocation.direction=="upstream" else (FinanceDownstreamInvoice if allocation.downstream_contract_id else FinanceManagementInvoice)
            snapshot.append({"allocation_id":allocation.id,"formal_invoice_id":allocation.formal_invoice_id,"amount":str(allocation.amount)})
            if allocation.formal_invoice_id:
                formal=await self.db.get(table,allocation.formal_invoice_id)
                if formal:
                    formal.original_amount=formal.amount; formal.amount=0; formal.posting_status="cleared"; formal.cleared_at=datetime.utcnow(); formal.clear_reason=reason
            allocation.status="cleared"
        item.confirmation_status="cleared"; item.clear_reason=reason; item.cleared_by=user.id; item.cleared_at=datetime.utcnow()
        await create_audit_log(self.db,user,"DELETE","发票挂账",item.id,description=reason,old_values={"records":snapshot})
        await self.db.commit(); return item

    async def delete_failed_item(self, item_id: int, user: User) -> None:
        item=await self._get_item_for_user(item_id,user)
        if item.parse_status != "failed" or item.confirmation_status != "draft" or any(a.formal_invoice_id for a in item.allocations):
            raise ValidationError(message="只有未生成正式记录的失败文件可以删除")
        keys=[item.pdf_file_key,item.ofd_file_key,item.xml_file_key]
        try:
            for key in filter(None,keys): get_minio_client().remove_object(settings.MINIO_BUCKET_CONTRACTS,key)
        except Exception as exc:
            item.error_message=f"源文件删除失败，可重试：{type(exc).__name__}";await self.db.commit();raise ValidationError(message="源文件删除失败，数据库记录已保留，请重试")
        await self.db.delete(item); await create_audit_log(self.db,user,"DELETE","发票失败文件",item_id); await self.db.commit()

    async def create_batch_from_upload(self, file: UploadFile, user: User) -> InvoiceImportBatch:
        filename = file.filename or ""
        if not filename.lower().endswith(".zip"):
            raise ValidationError(message="文件格式错误", field_errors={"file": "只支持 zip 压缩包"})

        content = BytesIO()
        total_size = 0
        while True:
            chunk = await file.read(_CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE:
                raise ValidationError(message="文件过大", field_errors={"file": "发票批次压缩包超过大小限制"})
            content.write(chunk)
        content_bytes = content.getvalue()

        now = datetime.utcnow()
        batch_token = uuid.uuid4().hex
        object_key = f"invoices/imports/batches/{now.strftime('%Y/%m')}/{uuid.uuid4()}.zip"
        batch = InvoiceImportBatch(
            batch_number=f"INVIMP-{now.strftime('%Y%m%d%H%M%S')}-{batch_token[:12].upper()}",
            original_filename=filename,
            archive_file_path=object_key,
            archive_file_key=object_key,
            status="uploaded",
            uploaded_by=user.id,
        )
        await self._put_bytes_to_minio(batch.archive_file_key, content_bytes, "application/zip")
        try:
            self.db.add(batch)
            await self.db.commit()
            await self.db.refresh(batch)
        except Exception:
            await self.db.rollback()
            self._remove_minio_object(batch.archive_file_key)
            raise
        _apply_confirmed_count(batch, 0)
        return batch

    async def process_uploaded_batch(self, batch_id: int) -> None:
        batch = await self.get_batch(batch_id)
        content = await self._get_bytes_from_minio(batch.archive_file_key)
        parsed_count = 0
        failed_count = 0
        duplicate_count = 0

        batch.status = "processing"
        await self.db.commit()

        with tempfile.TemporaryDirectory(prefix="invoice-import-") as tmp:
            work_dir = Path(tmp)
            try:
                packages = extract_invoice_archives(BytesIO(content), work_dir, batch.original_filename)
            except UnsafeArchiveError as exc:
                batch.status = "failed"
                batch.failed_items = 1
                await self.db.commit()
                raise ValidationError(message="发票压缩包不安全或格式错误", field_errors={"file": str(exc)}) from exc

            for package in packages:
                try:
                    async with self.db.begin_nested():
                        duplicate_found = await self._process_package(batch, package)
                    parsed_count += 1
                    if duplicate_found:
                        duplicate_count += 1
                except Exception as exc:  # item-level parse/import failure
                    failed_count += 1
                    async with self.db.begin_nested():
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

            batch.total_items = len(packages)
            batch.parsed_items = parsed_count
            batch.failed_items = failed_count
            batch.duplicate_items = duplicate_count
            batch.status = "completed_with_errors" if failed_count else "completed"
            batch.processed_at = datetime.utcnow()
            await self.db.commit()

    async def _process_package(self, batch: InvoiceImportBatch, package: ExtractedInvoicePackage) -> bool:
        xml_bytes = package.xml_path.read_bytes()
        parsed = parse_invoice_xml(xml_bytes)
        dedupe_key = build_dedupe_key(parsed)
        direction = detect_direction(parsed, settings.COMPANY_TAX_NO)
        duplicate = await self._find_duplicate(dedupe_key)
        pdf_key = await self._store_package_file(batch, package.pdf_path, "application/pdf")
        ofd_key = await self._store_package_file(batch, package.ofd_path, "application/octet-stream")
        xml_key = await self._store_package_file(batch, package.xml_path, "application/xml")
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
            tax_rate=parsed.tax_rate,
            tax_amount=parsed.tax_amount,
            total_amount=parsed.total_amount,
            invoice_type=parsed.invoice_type,
            remarks=parsed.remarks,
            project_name=parsed.project_name,
            construction_project_name=parsed.construction_project_name,
            dedupe_key=dedupe_key,
            duplicate_of_item_id=duplicate.id if duplicate else None,
            direction=direction,
            parse_status="parsed",
            match_status="not_matched",
            confirmation_status="draft",
            pdf_file_path=pdf_key,
            pdf_file_key=pdf_key,
            ofd_file_path=ofd_key,
            ofd_file_key=ofd_key,
            xml_file_path=xml_key,
            xml_file_key=xml_key,
            raw_xml=xml_bytes.decode("utf-8", errors="ignore"),
            parsed_payload=parsed.payload,
        )
        self.db.add(item)
        await self.db.flush()
        candidates = await InvoiceMatchService(self.db).find_candidates(item)
        item.match_status = "matched" if candidates else "not_matched"
        for candidate in candidates:
            self.db.add(candidate)
        return duplicate is not None

    async def _get_item_for_user(self, item_id: int, user: User) -> InvoiceImportItem:
        result = await self.db.execute(
            select(InvoiceImportItem)
            .options(selectinload(InvoiceImportItem.batch))
            .where(InvoiceImportItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item or (not _can_access_all_imports(user) and item.batch.uploaded_by != user.id):
            raise ResourceNotFoundError(resource_type="导入发票", resource_id=item_id)
        return item

    def _validate_allocation_target(self, direction: str, upstream_contract_id: int | None, downstream_contract_id: int | None, management_contract_id: int | None = None) -> None:
        if direction == InvoiceDirection.UPSTREAM or direction == "upstream":
            if not upstream_contract_id or downstream_contract_id or management_contract_id:
                raise ValidationError(message="上游分摊必须且只能选择上游合同", field_errors={"upstream_contract_id": "请选择上游合同"})
            return
        if direction == InvoiceDirection.DOWNSTREAM or direction == "downstream":
            if bool(downstream_contract_id) == bool(management_contract_id) or upstream_contract_id:
                raise ValidationError(message="进项发票分摊目标无效", field_errors={"downstream_contract_id": "请选择下游或管理合同之一"})
            return
        raise ValidationError(message="分摊方向必须为上游或下游", field_errors={"direction": "分摊方向无效"})

    async def _store_package_file(self, batch: InvoiceImportBatch, path: Path | None, content_type: str) -> str | None:
        if not path:
            return None
        suffix = path.suffix.lower() or ".bin"
        object_key = f"invoices/imports/items/{batch.batch_number}/{uuid.uuid4()}{suffix}"
        await self._put_bytes_to_minio(object_key, path.read_bytes(), content_type)
        return object_key

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

    def _remove_minio_object(self, object_key: str) -> None:
        try:
            get_minio_client().remove_object(settings.MINIO_BUCKET_CONTRACTS, object_key)
        except Exception:
            pass

    async def _get_bytes_from_minio(self, object_key: str) -> bytes:
        client = get_minio_client()
        response = client.get_object(settings.MINIO_BUCKET_CONTRACTS, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
