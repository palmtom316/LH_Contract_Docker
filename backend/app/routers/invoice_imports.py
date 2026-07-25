"""Electronic invoice import workbench API."""
from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.invoice_import import (
    AllocationCreate,
    AllocationResponse,
    AllocationUpdate,
    BatchResponse,
    ConfirmItemRequest,
    IgnoreItemRequest,
    ClearInvoiceRequest,
    ImportItemResponse,
)
from app.services.invoice_import.posting import InvoicePostingService
from app.services.invoice_import.service import InvoiceImportService

router = APIRouter()


def get_import_service(db: AsyncSession = Depends(get_db)) -> InvoiceImportService:
    return InvoiceImportService(db)


@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_batch(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    batch = await service.create_batch_from_upload(file, current_user)
    return batch


@router.get("/batches", response_model=list[BatchResponse])
async def list_batches(
    current_user: User = Depends(require_permission(Permission.VIEW_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.list_batches(current_user)


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.get_batch(batch_id, current_user)


@router.get("/batches/{batch_id}/items", response_model=list[ImportItemResponse])
async def list_items(
    batch_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.list_items(batch_id, current_user)


@router.delete("/batches/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: int,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    await service.delete_batch(batch_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/batches/{batch_id}/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_batch(
    batch_id: int,
    request: ClearInvoiceRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    await service.clear_batch(batch_id, request.reason, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/items/{item_id}/allocations", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    item_id: int,
    allocation_in: AllocationCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.create_allocation(item_id, allocation_in, current_user)


@router.put("/allocations/{allocation_id}", response_model=AllocationResponse)
async def update_allocation(
    allocation_id: int,
    allocation_in: AllocationUpdate,
    current_user: User = Depends(require_permission(Permission.EDIT_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.update_allocation(allocation_id, allocation_in, current_user)


@router.post("/items/{item_id}/confirm", response_model=ImportItemResponse)
async def confirm_item(
    item_id: int,
    request: ConfirmItemRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    db: AsyncSession = Depends(get_db),
):
    return await InvoicePostingService(db).confirm_item(item_id, current_user, request.override_duplicate)

@router.post("/items/{item_id}/ignore", response_model=ImportItemResponse)
async def ignore_item(
    item_id: int,
    request: IgnoreItemRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.ignore_item(item_id, request.reason, current_user)

@router.post("/items/{item_id}/clear", response_model=ImportItemResponse)
async def clear_item(
    item_id: int,
    request: ClearInvoiceRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    return await service.clear_posting(item_id, request.reason, current_user)

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_failed_item(
    item_id: int,
    current_user: User = Depends(require_permission(Permission.CREATE_INVOICES)),
    service: InvoiceImportService = Depends(get_import_service),
):
    await service.delete_failed_item(item_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
