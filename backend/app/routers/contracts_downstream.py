"""
Downstream Contract Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date
from datetime import datetime, date
import io
import urllib.parse
from openpyxl import Workbook

from app.database import get_db
from app.models.user import User
from app.models.contract_downstream import (
    FinanceDownstreamPayable, FinanceDownstreamInvoice,
    FinanceDownstreamPayment, DownstreamSettlement
)
from app.schemas.contract_downstream import (
    ContractDownstreamCreate, ContractDownstreamUpdate, ContractDownstreamResponse, ContractDownstreamListResponse,
    PayableCreate, PayableResponse,
    InvoiceDownstreamCreate, InvoiceDownstreamResponse,
    PaymentCreate, PaymentResponse,
    DownstreamSettlementCreate, DownstreamSettlementResponse
)
from app.services.auth import get_current_active_user
from app.services.contract_downstream_service import ContractDownstreamService
from app.core.permissions import require_permission, Permission
from app.core.errors import ResourceNotFoundError, ValidationError, DatabaseError

router = APIRouter()

# Dependency to get service
def get_contract_service(db: AsyncSession = Depends(get_db)) -> ContractDownstreamService:
    return ContractDownstreamService(db)


@router.get("/export/excel", response_class=StreamingResponse)
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_DOWNSTREAM_BASIC_INFO)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """Export downstream contracts to Excel"""
    try:
        contracts = await service.list_all_contracts(keyword, status, start_date, end_date, category)
        
        # Create Excel in memory using openpyxl directly (Memory Optimized)
        wb = Workbook(write_only=True)
        ws = wb.create_sheet("下游合同")
        
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
        
        filename = f"downstream_contracts_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
            
    except Exception as e:
        raise DatabaseError(
            message="导出失败",
            detail=f"无法导出合同数据: {str(e)}"
        )


# ===== Contract Operations =====

@router.get("/", response_model=ContractDownstreamListResponse)
async def list_contracts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_DOWNSTREAM_BASIC_INFO)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """List downstream contracts with pagination and filtering"""
    return await service.list_contracts(page, page_size, keyword, status, start_date, end_date, category)


@router.post("/", response_model=ContractDownstreamResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractDownstreamCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_DOWNSTREAM_CONTRACTS)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """Create new downstream contract"""
    return await service.create_contract(contract_in, current_user)


@router.get("/{contract_id}", response_model=ContractDownstreamResponse)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_DOWNSTREAM_BASIC_INFO)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """Get contract details"""
    contract = await service.get_contract(contract_id)
    if not contract:
        raise ResourceNotFoundError(
            resource_type="下游合同",
            resource_id=contract_id
        )
    return contract


@router.put("/{contract_id}", response_model=ContractDownstreamResponse)
async def update_contract(
    contract_id: int,
    contract_in: ContractDownstreamUpdate,
    current_user: User = Depends(require_permission(Permission.EDIT_DOWNSTREAM_CONTRACTS)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """Update contract"""
    return await service.update_contract(contract_id, contract_in, current_user)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(require_permission(Permission.DELETE_DOWNSTREAM_CONTRACTS)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """Delete contract"""
    await service.delete_contract(contract_id, current_user)
    return {"message": "合同已删除"}



# ===== Sub-resource Operations =====

# 1. Payables (应付款)
@router.post("/{contract_id}/payables", response_model=PayableResponse)
async def create_payable(
    contract_id: int,
    payable_in: PayableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    if contract_id != payable_in.contract_id:
        raise ValidationError(
            message="合同ID不匹配",
            field_errors={"contract_id": "请求路径和数据中的合同ID不一致"}
        )
        
    payable = FinanceDownstreamPayable(**payable_in.model_dump(), created_by=current_user.id, updated_by=current_user.id)
    db.add(payable)
    await db.commit()
    await db.refresh(payable)
    
    await service.refresh_contract_status(contract_id)
    
    return payable


@router.get("/{contract_id}/payables", response_model=List[PayableResponse])
async def list_payables(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceDownstreamPayable).where(FinanceDownstreamPayable.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/payables/{payable_id}", response_model=PayableResponse)
async def update_payable(
    contract_id: int,
    payable_id: int,
    payable_in: PayableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    query = select(FinanceDownstreamPayable).where(
        FinanceDownstreamPayable.id == payable_id,
        FinanceDownstreamPayable.contract_id == contract_id
    )
    result = await db.execute(query)
    payable = result.scalar_one_or_none()
    if not payable:
        raise ResourceNotFoundError(
            resource_type="应付款记录",
            resource_id=payable_id
        )
    
    for key, value in payable_in.model_dump(exclude={'contract_id'}).items():
        setattr(payable, key, value)
    payable.updated_by = current_user.id
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
    service: ContractDownstreamService = Depends(get_contract_service)
):
    query = select(FinanceDownstreamPayable).where(
        FinanceDownstreamPayable.id == payable_id,
        FinanceDownstreamPayable.contract_id == contract_id
    )
    result = await db.execute(query)
    payable = result.scalar_one_or_none()
    if not payable:
        raise ResourceNotFoundError(
            resource_type="应付款记录",
            resource_id=payable_id
        )
    
    await db.delete(payable)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}


# 2. Invoices (收票)
@router.post("/{contract_id}/invoices", response_model=InvoiceDownstreamResponse)
async def create_invoice(
    contract_id: int,
    invoice_in: InvoiceDownstreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != invoice_in.contract_id:
        raise ValidationError(
            message="合同ID不匹配",
            field_errors={"contract_id": "请求路径和数据中的合同ID不一致"}
        )
        
    invoice = FinanceDownstreamInvoice(**invoice_in.model_dump(), created_by=current_user.id, updated_by=current_user.id)
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/{contract_id}/invoices", response_model=List[InvoiceDownstreamResponse])
async def list_invoices(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceDownstreamInvoice).where(FinanceDownstreamInvoice.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/invoices/{invoice_id}", response_model=InvoiceDownstreamResponse)
async def update_invoice(
    contract_id: int,
    invoice_id: int,
    invoice_in: InvoiceDownstreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceDownstreamInvoice).where(
        FinanceDownstreamInvoice.id == invoice_id,
        FinanceDownstreamInvoice.contract_id == contract_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ResourceNotFoundError(
            resource_type="发票记录",
            resource_id=invoice_id
        )
    
    for key, value in invoice_in.model_dump(exclude={'contract_id'}).items():
        setattr(invoice, key, value)
    invoice.updated_by = current_user.id
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
    query = select(FinanceDownstreamInvoice).where(
        FinanceDownstreamInvoice.id == invoice_id,
        FinanceDownstreamInvoice.contract_id == contract_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ResourceNotFoundError(
            resource_type="发票记录",
            resource_id=invoice_id
        )
    
    await db.delete(invoice)
    await db.commit()
    return {"message": "删除成功"}


# 3. Payments (付款)
@router.post("/{contract_id}/payments", response_model=PaymentResponse)
async def create_payment(
    contract_id: int,
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    if contract_id != payment_in.contract_id:
        raise ValidationError(
            message="合同ID不匹配",
            field_errors={"contract_id": "请求路径和数据中的合同ID不一致"}
        )
        
    payment = FinanceDownstreamPayment(**payment_in.model_dump(), created_by=current_user.id, updated_by=current_user.id)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    await service.refresh_contract_status(contract_id)
    return payment


@router.get("/{contract_id}/payments", response_model=List[PaymentResponse])
async def list_payments(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceDownstreamPayment).where(FinanceDownstreamPayment.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    contract_id: int,
    payment_id: int,
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    query = select(FinanceDownstreamPayment).where(
        FinanceDownstreamPayment.id == payment_id,
        FinanceDownstreamPayment.contract_id == contract_id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise ResourceNotFoundError(
            resource_type="付款记录",
            resource_id=payment_id
        )
    
    for key, value in payment_in.model_dump(exclude={'contract_id'}).items():
        setattr(payment, key, value)
    payment.updated_by = current_user.id
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
    service: ContractDownstreamService = Depends(get_contract_service)
):
    query = select(FinanceDownstreamPayment).where(
        FinanceDownstreamPayment.id == payment_id,
        FinanceDownstreamPayment.contract_id == contract_id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise ResourceNotFoundError(
            resource_type="付款记录",
            resource_id=payment_id
        )
    
    await db.delete(payment)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}


# 4. Settlements (结算)
@router.post("/{contract_id}/settlements", response_model=DownstreamSettlementResponse)
async def create_settlement(
    contract_id: int,
    settlement_in: DownstreamSettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    if contract_id != settlement_in.contract_id:
        raise ValidationError(
            message="合同ID不匹配",
            field_errors={"contract_id": "请求路径和数据中的合同ID不一致"}
        )
        
    settlement = DownstreamSettlement(**settlement_in.model_dump(), created_by=current_user.id, updated_by=current_user.id)
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    
    await service.refresh_contract_status(contract_id)
    return settlement


@router.get("/{contract_id}/settlements", response_model=List[DownstreamSettlementResponse])
async def list_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(DownstreamSettlement).where(DownstreamSettlement.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/settlements/{settlement_id}", response_model=DownstreamSettlementResponse)
async def update_settlement(
    contract_id: int,
    settlement_id: int,
    settlement_in: DownstreamSettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    query = select(DownstreamSettlement).where(
        DownstreamSettlement.id == settlement_id,
        DownstreamSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise ResourceNotFoundError(
            resource_type="结算记录",
            resource_id=settlement_id
        )
    
    for key, value in settlement_in.model_dump(exclude={'contract_id'}).items():
        setattr(settlement, key, value)
    settlement.updated_by = current_user.id
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
    service: ContractDownstreamService = Depends(get_contract_service)
):
    query = select(DownstreamSettlement).where(
        DownstreamSettlement.id == settlement_id,
        DownstreamSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise ResourceNotFoundError(
            resource_type="结算记录",
            resource_id=settlement_id
        )
    
    await db.delete(settlement)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}
