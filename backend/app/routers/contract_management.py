"""
Management Contract Management Router
Refactored to use standardized AppException
"""
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date
import io
import urllib.parse
from openpyxl import Workbook

from app.database import get_db
from app.models.user import User
from app.models.contract_management import (
    FinanceManagementPayable, FinanceManagementInvoice,
    FinanceManagementPayment, ManagementSettlement
)
from app.schemas.contract_management import (
    ContractManagementCreate, ContractManagementUpdate, ContractManagementResponse, ContractManagementListResponse,
    ManagementPayableCreate, ManagementPayableResponse,
    ManagementInvoiceCreate, ManagementInvoiceResponse,
    ManagementPaymentCreate, ManagementPaymentResponse,
    ManagementSettlementCreate, ManagementSettlementResponse
)
from app.services.auth import get_current_active_user
from app.services.contract_management_service import ContractManagementService
from app.core.permissions import require_permission, Permission
from app.core.errors import ResourceNotFoundError, ValidationError, DatabaseError

router = APIRouter()

# Dependency
def get_contract_service(db: AsyncSession = Depends(get_db)) -> ContractManagementService:
    return ContractManagementService(db)


@router.get("/export/excel", response_class=StreamingResponse)
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_MANAGEMENT_BASIC_INFO)),
    service: ContractManagementService = Depends(get_contract_service)
):
    """Export management contracts to Excel"""
    try:
        contracts = await service.list_all_contracts(keyword, status, start_date, end_date, category)
        
        # Create Excel in memory using openpyxl directly (Memory Optimized)
        wb = Workbook(write_only=True)
        ws = wb.create_sheet("管理合同")
        
        # Header
        headers = [
            "合同序号", "合同编号", "合同名称", "甲方", "乙方", "合同类别",
            "计价模式", "合同金额", "应付款金额", "挂账金额", "付款金额",
            "结算金额", "签订日期", "状态", "备注"
        ]
        ws.append(headers)
        
        # Rows
        for c in contracts:
            pricing_val = c.pricing_mode.value if hasattr(c.pricing_mode, 'value') else c.pricing_mode
            
            row = [
                c.serial_number,
                c.contract_code,
                c.contract_name,
                c.party_a_name,
                c.party_b_name,
                c.category,
                pricing_val,
                float(c.contract_amount),
                float(c.total_payable) if c.total_payable else 0,
                float(c.total_invoiced) if c.total_invoiced else 0,
                float(c.total_paid) if c.total_paid else 0,
                float(c.total_settlement) if c.total_settlement else 0,
                c.sign_date,
                c.status,
                c.notes
            ]
            ws.append(row)
            
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        
        filename = f"management_contracts_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise DatabaseError(message="导出失败", detail=str(e))


# ===== Contract Operations =====

@router.get("/", response_model=ContractManagementListResponse)
async def list_contracts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_MANAGEMENT_BASIC_INFO)),
    service: ContractManagementService = Depends(get_contract_service)
):
    """List management contracts with pagination and filtering"""
    return await service.list_contracts(page, page_size, keyword, status, start_date, end_date, category)


@router.post("/", response_model=ContractManagementResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractManagementCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_MANAGEMENT_CONTRACTS)),
    service: ContractManagementService = Depends(get_contract_service)
):
    """Create new management contract"""
    return await service.create_contract(contract_in, current_user)


@router.get("/{contract_id}", response_model=ContractManagementResponse)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_MANAGEMENT_BASIC_INFO)),
    service: ContractManagementService = Depends(get_contract_service)
):
    """Get contract details"""
    contract = await service.get_contract(contract_id)
    if not contract:
        raise ResourceNotFoundError(resource_type="管理合同", resource_id=contract_id)
    return contract


@router.put("/{contract_id}", response_model=ContractManagementResponse)
async def update_contract(
    contract_id: int,
    contract_in: ContractManagementUpdate,
    current_user: User = Depends(require_permission(Permission.EDIT_MANAGEMENT_CONTRACTS)),
    service: ContractManagementService = Depends(get_contract_service)
):
    """Update contract"""
    return await service.update_contract(contract_id, contract_in, current_user)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(require_permission(Permission.DELETE_MANAGEMENT_CONTRACTS)),
    service: ContractManagementService = Depends(get_contract_service)
):
    """Delete contract"""
    await service.delete_contract(contract_id, current_user)
    return {"message": "合同已删除"}



# ===== Sub-resource Operations =====

# 1. Payables (应付款)
@router.post("/{contract_id}/payables", response_model=ManagementPayableResponse)
async def create_payable(
    contract_id: int,
    payable_in: ManagementPayableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    if contract_id != payable_in.contract_id:
        raise ValidationError(message="合同ID不匹配", field_errors={"contract_id": "路径参数与请求体中的合同ID不一致"})
        
    payable = FinanceManagementPayable(**payable_in.model_dump())
    db.add(payable)
    await db.commit()
    await db.refresh(payable)
    
    await service.refresh_contract_status(contract_id)
    return payable


@router.get("/{contract_id}/payables", response_model=List[ManagementPayableResponse])
async def list_payables(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayable).where(FinanceManagementPayable.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/payables/{payable_id}", response_model=ManagementPayableResponse)
async def update_payable(
    contract_id: int,
    payable_id: int,
    payable_in: ManagementPayableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    query = select(FinanceManagementPayable).where(
        FinanceManagementPayable.id == payable_id,
        FinanceManagementPayable.contract_id == contract_id
    )
    result = await db.execute(query)
    payable = result.scalar_one_or_none()
    if not payable:
        raise ResourceNotFoundError(resource_type="应付款记录", resource_id=payable_id)
    
    for key, value in payable_in.model_dump(exclude={'contract_id'}).items():
        setattr(payable, key, value)
    await db.commit()
    await db.refresh(payable)
    
    await service.refresh_contract_status(contract_id)
    return payable


@router.delete("/{contract_id}/payables/{payable_id}")
async def delete_payable(
    contract_id: int,
    payable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    query = select(FinanceManagementPayable).where(
        FinanceManagementPayable.id == payable_id,
        FinanceManagementPayable.contract_id == contract_id
    )
    result = await db.execute(query)
    payable = result.scalar_one_or_none()
    if not payable:
        raise ResourceNotFoundError(resource_type="应付款记录", resource_id=payable_id)
    
    await db.delete(payable)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}


# 2. Invoices (收票/挂账)
@router.post("/{contract_id}/invoices", response_model=ManagementInvoiceResponse)
async def create_invoice(
    contract_id: int,
    invoice_in: ManagementInvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != invoice_in.contract_id:
        raise ValidationError(message="合同ID不匹配", field_errors={"contract_id": "路径参数与请求体中的合同ID不一致"})
        
    invoice = FinanceManagementInvoice(**invoice_in.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/{contract_id}/invoices", response_model=List[ManagementInvoiceResponse])
async def list_invoices(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementInvoice).where(FinanceManagementInvoice.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/invoices/{invoice_id}", response_model=ManagementInvoiceResponse)
async def update_invoice(
    contract_id: int,
    invoice_id: int,
    invoice_in: ManagementInvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementInvoice).where(
        FinanceManagementInvoice.id == invoice_id,
        FinanceManagementInvoice.contract_id == contract_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ResourceNotFoundError(resource_type="发票记录", resource_id=invoice_id)
    
    for key, value in invoice_in.model_dump(exclude={'contract_id'}).items():
        setattr(invoice, key, value)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.delete("/{contract_id}/invoices/{invoice_id}")
async def delete_invoice(
    contract_id: int,
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementInvoice).where(
        FinanceManagementInvoice.id == invoice_id,
        FinanceManagementInvoice.contract_id == contract_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ResourceNotFoundError(resource_type="发票记录", resource_id=invoice_id)
    
    await db.delete(invoice)
    await db.commit()
    return {"message": "删除成功"}


# 3. Payments (付款)
@router.post("/{contract_id}/payments", response_model=ManagementPaymentResponse)
async def create_payment(
    contract_id: int,
    payment_in: ManagementPaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    if contract_id != payment_in.contract_id:
        raise ValidationError(message="合同ID不匹配", field_errors={"contract_id": "路径参数与请求体中的合同ID不一致"})
        
    payment = FinanceManagementPayment(**payment_in.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    await service.refresh_contract_status(contract_id)
    return payment


@router.get("/{contract_id}/payments", response_model=List[ManagementPaymentResponse])
async def list_payments(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayment).where(FinanceManagementPayment.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/payments/{payment_id}", response_model=ManagementPaymentResponse)
async def update_payment(
    contract_id: int,
    payment_id: int,
    payment_in: ManagementPaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    query = select(FinanceManagementPayment).where(
        FinanceManagementPayment.id == payment_id,
        FinanceManagementPayment.contract_id == contract_id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise ResourceNotFoundError(resource_type="付款记录", resource_id=payment_id)
    
    for key, value in payment_in.model_dump(exclude={'contract_id'}).items():
        setattr(payment, key, value)
    await db.commit()
    await db.refresh(payment)
    
    await service.refresh_contract_status(contract_id)
    return payment


@router.delete("/{contract_id}/payments/{payment_id}")
async def delete_payment(
    contract_id: int,
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    query = select(FinanceManagementPayment).where(
        FinanceManagementPayment.id == payment_id,
        FinanceManagementPayment.contract_id == contract_id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise ResourceNotFoundError(resource_type="付款记录", resource_id=payment_id)
    
    await db.delete(payment)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}


# 4. Settlements (结算)
@router.post("/{contract_id}/settlements", response_model=ManagementSettlementResponse)
async def create_settlement(
    contract_id: int,
    settlement_in: ManagementSettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    if contract_id != settlement_in.contract_id:
        raise ValidationError(message="合同ID不匹配", field_errors={"contract_id": "路径参数与请求体中的合同ID不一致"})
        
    settlement = ManagementSettlement(**settlement_in.model_dump())
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    
    await service.refresh_contract_status(contract_id)
    return settlement


@router.get("/{contract_id}/settlements", response_model=List[ManagementSettlementResponse])
async def list_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(ManagementSettlement).where(ManagementSettlement.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/settlements/{settlement_id}", response_model=ManagementSettlementResponse)
async def update_settlement(
    contract_id: int,
    settlement_id: int,
    settlement_in: ManagementSettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    query = select(ManagementSettlement).where(
        ManagementSettlement.id == settlement_id,
        ManagementSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise ResourceNotFoundError(resource_type="结算记录", resource_id=settlement_id)
    
    for key, value in settlement_in.model_dump(exclude={'contract_id'}).items():
        setattr(settlement, key, value)
    await db.commit()
    await db.refresh(settlement)
    
    await service.refresh_contract_status(contract_id)
    return settlement


@router.delete("/{contract_id}/settlements/{settlement_id}")
async def delete_settlement(
    contract_id: int,
    settlement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractManagementService = Depends(get_contract_service)
):
    query = select(ManagementSettlement).where(
        ManagementSettlement.id == settlement_id,
        ManagementSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise ResourceNotFoundError(resource_type="结算记录", resource_id=settlement_id)
    
    await db.delete(settlement)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}
