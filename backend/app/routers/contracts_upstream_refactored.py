"""
Upstream Contract Management Router - REFACTORED
Demonstrates optimized code using generic sub-resource service
"""
from fastapi import APIRouter, Depends, status, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import pandas as pd
import io
import os
import urllib.parse
import logging

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import (
    FinanceUpstreamReceivable, FinanceUpstreamInvoice,
    FinanceUpstreamReceipt, ProjectSettlement
)
from app.schemas.contract_upstream import (
    ContractUpstreamCreate, ContractUpstreamUpdate, ContractUpstreamResponse, ContractUpstreamListResponse,
    ReceivableCreate, ReceivableResponse,
    InvoiceUpstreamCreate, InvoiceUpstreamResponse,
    ReceiptCreate, ReceiptResponse,
    SettlementCreate, SettlementResponse
)
from app.services.auth import get_current_active_user
from app.services.contract_upstream_service import ContractUpstreamService
from app.services.base_subresource_service import SubResourceService
from app.core.permissions import require_permission, Permission
from app.core.errors import ResourceNotFoundError, ValidationError, DatabaseError

logger = logging.getLogger(__name__)
router = APIRouter()

# Service dependencies
def get_contract_service(db: AsyncSession = Depends(get_db)) -> ContractUpstreamService:
    return ContractUpstreamService(db)

def get_receivable_service(db: AsyncSession = Depends(get_db)) -> SubResourceService:
    return SubResourceService(db, FinanceUpstreamReceivable, "应收款记录")

def get_invoice_service(db: AsyncSession = Depends(get_db)) -> SubResourceService:
    return SubResourceService(db, FinanceUpstreamInvoice, "发票记录")

def get_receipt_service(db: AsyncSession = Depends(get_db)) -> SubResourceService:
    return SubResourceService(db, FinanceUpstreamReceipt, "回款记录")

def get_settlement_service(db: AsyncSession = Depends(get_db)) -> SubResourceService:
    return SubResourceService(db, ProjectSettlement, "结算记录")


# ===== Contract Operations (unchanged) =====

@router.get("/", response_model=ContractUpstreamListResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_UPSTREAM_BASIC_INFO)),
    service: ContractUpstreamService = Depends(get_contract_service)
):
    """List upstream contracts with pagination and filtering"""
    return await service.list_contracts(page, page_size, keyword, status, start_date, end_date)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractUpstreamCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_UPSTREAM_CONTRACTS)),
    service: ContractUpstreamService = Depends(get_contract_service)
):
    """Create new upstream contract"""
    contract = await service.create_contract(contract_in, current_user)
    return {
        "id": contract.id,
        "serial_number": contract.serial_number,
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name,
        "party_a_name": contract.party_a_name,
        "party_b_name": contract.party_b_name,
        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0.0,
        "sign_date": contract.sign_date.isoformat() if contract.sign_date else None,
        "status": contract.status,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
    }


@router.get("/{contract_id}", response_model=ContractUpstreamResponse)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_UPSTREAM_BASIC_INFO)),
    service: ContractUpstreamService = Depends(get_contract_service)
):
    """Get contract details"""
    contract = await service.get_contract(contract_id)
    if not contract:
        raise ResourceNotFoundError(resource_type="上游合同", resource_id=contract_id)
    return contract


@router.put("/{contract_id}")
async def update_contract(
    contract_id: int,
    contract_in: ContractUpstreamUpdate,
    current_user: User = Depends(require_permission(Permission.EDIT_UPSTREAM_CONTRACTS)),
    service: ContractUpstreamService = Depends(get_contract_service)
):
    """Update contract"""
    return await service.update_contract(contract_id, contract_in, current_user)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(require_permission(Permission.DELETE_UPSTREAM_CONTRACTS)),
    service: ContractUpstreamService = Depends(get_contract_service)
):
    """Delete contract"""
    await service.delete_contract(contract_id, current_user)
    return {"message": "合同已删除"}


# ===== Sub-resource Operations - REFACTORED =====

# 1. Receivables (应收款) - Using Generic Service
@router.post("/{contract_id}/receivables", response_model=ReceivableResponse)
async def create_receivable(
    contract_id: int,
    receivable_in: ReceivableCreate,
    current_user: User = Depends(get_current_active_user),
    receivable_service: SubResourceService = Depends(get_receivable_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    receivable = await receivable_service.create(contract_id, receivable_in.model_dump(), current_user.id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return receivable


@router.get("/{contract_id}/receivables", response_model=List[ReceivableResponse])
async def list_receivables(
    contract_id: int,
    receivable_service: SubResourceService = Depends(get_receivable_service)
):
    return await receivable_service.list_by_contract(contract_id)


@router.put("/{contract_id}/receivables/{receivable_id}", response_model=ReceivableResponse)
async def update_receivable(
    contract_id: int,
    receivable_id: int,
    receivable_in: ReceivableCreate,
    current_user: User = Depends(get_current_active_user),
    receivable_service: SubResourceService = Depends(get_receivable_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    receivable = await receivable_service.update(contract_id, receivable_id, receivable_in.model_dump(), current_user.id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return receivable


@router.delete("/{contract_id}/receivables/{receivable_id}")
async def delete_receivable(
    contract_id: int,
    receivable_id: int,
    receivable_service: SubResourceService = Depends(get_receivable_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    await receivable_service.delete(contract_id, receivable_id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return {"message": "删除成功"}


# 2. Invoices (开票) - Using Generic Service
@router.post("/{contract_id}/invoices", response_model=InvoiceUpstreamResponse)
async def create_invoice(
    contract_id: int,
    invoice_in: InvoiceUpstreamCreate,
    current_user: User = Depends(get_current_active_user),
    invoice_service: SubResourceService = Depends(get_invoice_service)
):
    return await invoice_service.create(contract_id, invoice_in.model_dump(), current_user.id)


@router.get("/{contract_id}/invoices", response_model=List[InvoiceUpstreamResponse])
async def list_invoices(
    contract_id: int,
    invoice_service: SubResourceService = Depends(get_invoice_service)
):
    return await invoice_service.list_by_contract(contract_id)


@router.put("/{contract_id}/invoices/{invoice_id}", response_model=InvoiceUpstreamResponse)
async def update_invoice(
    contract_id: int,
    invoice_id: int,
    invoice_in: InvoiceUpstreamCreate,
    current_user: User = Depends(get_current_active_user),
    invoice_service: SubResourceService = Depends(get_invoice_service)
):
    return await invoice_service.update(contract_id, invoice_id, invoice_in.model_dump(), current_user.id)


@router.delete("/{contract_id}/invoices/{invoice_id}")
async def delete_invoice(
    contract_id: int,
    invoice_id: int,
    invoice_service: SubResourceService = Depends(get_invoice_service)
):
    await invoice_service.delete(contract_id, invoice_id)
    return {"message": "删除成功"}


# 3. Receipts (收款) - Using Generic Service
@router.post("/{contract_id}/receipts", response_model=ReceiptResponse)
async def create_receipt(
    contract_id: int,
    receipt_in: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    receipt_service: SubResourceService = Depends(get_receipt_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    receipt = await receipt_service.create(contract_id, receipt_in.model_dump(), current_user.id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return receipt


@router.get("/{contract_id}/receipts", response_model=List[ReceiptResponse])
async def list_receipts(
    contract_id: int,
    receipt_service: SubResourceService = Depends(get_receipt_service)
):
    return await receipt_service.list_by_contract(contract_id)


@router.put("/{contract_id}/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    contract_id: int,
    receipt_id: int,
    receipt_in: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    receipt_service: SubResourceService = Depends(get_receipt_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    receipt = await receipt_service.update(contract_id, receipt_id, receipt_in.model_dump(), current_user.id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return receipt


@router.delete("/{contract_id}/receipts/{receipt_id}")
async def delete_receipt(
    contract_id: int,
    receipt_id: int,
    receipt_service: SubResourceService = Depends(get_receipt_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    await receipt_service.delete(contract_id, receipt_id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return {"message": "删除成功"}


# 4. Settlements (结算) - Using Generic Service
@router.post("/{contract_id}/settlements", response_model=SettlementResponse)
async def create_settlement(
    contract_id: int,
    settlement_in: SettlementCreate,
    current_user: User = Depends(get_current_active_user),
    settlement_service: SubResourceService = Depends(get_settlement_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    settlement = await settlement_service.create(contract_id, settlement_in.model_dump(), current_user.id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return settlement


@router.get("/{contract_id}/settlements", response_model=List[SettlementResponse])
async def list_settlements(
    contract_id: int,
    settlement_service: SubResourceService = Depends(get_settlement_service)
):
    return await settlement_service.list_by_contract(contract_id)


@router.put("/{contract_id}/settlements/{settlement_id}", response_model=SettlementResponse)
async def update_settlement(
    contract_id: int,
    settlement_id: int,
    settlement_in: SettlementCreate,
    current_user: User = Depends(get_current_active_user),
    settlement_service: SubResourceService = Depends(get_settlement_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    settlement = await settlement_service.update(contract_id, settlement_id, settlement_in.model_dump(), current_user.id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return settlement


@router.delete("/{contract_id}/settlements/{settlement_id}")
async def delete_settlement(
    contract_id: int,
    settlement_id: int,
    settlement_service: SubResourceService = Depends(get_settlement_service),
    contract_service: ContractUpstreamService = Depends(get_contract_service)
):
    await settlement_service.delete(contract_id, settlement_id)
    await contract_service.refresh_contract_status(contract_id)
    await contract_service._invalidate_dashboard_cache()
    return {"message": "删除成功"}
