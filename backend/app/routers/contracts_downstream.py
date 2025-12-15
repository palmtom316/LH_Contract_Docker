"""
Downstream Contract Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
import urllib.parse

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

router = APIRouter()

# Dependency to get service
def get_contract_service(db: AsyncSession = Depends(get_db)) -> ContractDownstreamService:
    return ContractDownstreamService(db)


@router.get("/export/excel", response_class=StreamingResponse)
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_DOWNSTREAM_BASIC_INFO)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """Export downstream contracts to Excel"""
    try:
        contracts = await service.list_all_contracts(keyword, status)
        
        # Create DataFrame
        data = []
        for c in contracts:
            data.append({
                "合同序号": c.serial_number,
                "系统编号": c.id,
                "合同编号": c.contract_code,
                "合同名称": c.contract_name,
                "甲方": c.party_a_name,
                "乙方": c.party_b_name,
                "合同类别": c.category,
                "计价模式": c.pricing_mode.value if hasattr(c.pricing_mode, 'value') else c.pricing_mode,
                "合同金额": float(c.contract_amount),
                "签订日期": c.sign_date,
                "状态": c.status,
                "备注": c.notes
            })
            
        df = pd.DataFrame(data)
        stream = io.BytesIO()
        # Use pandas to write Excel to the stream
        with pd.ExcelWriter(stream, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='下游合同')
            
        stream.seek(0)
        
        filename = f"downstream_contracts_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


# ===== Contract Operations =====

@router.get("/", response_model=ContractDownstreamListResponse)
async def list_contracts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_DOWNSTREAM_BASIC_INFO)),
    service: ContractDownstreamService = Depends(get_contract_service)
):
    """List downstream contracts with pagination and filtering"""
    return await service.list_contracts(page, page_size, keyword, status)


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
        raise HTTPException(status_code=404, detail="合同不存在")
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
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
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
        raise HTTPException(status_code=404, detail="应付款记录不存在")
    
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
        raise HTTPException(status_code=404, detail="应付款记录不存在")
    
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
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
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
        raise HTTPException(status_code=404, detail="发票记录不存在")
    
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
        raise HTTPException(status_code=404, detail="发票记录不存在")
    
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
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
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
        raise HTTPException(status_code=404, detail="付款记录不存在")
    
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
        raise HTTPException(status_code=404, detail="付款记录不存在")
    
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
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
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
        raise HTTPException(status_code=404, detail="结算记录不存在")
    
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
        raise HTTPException(status_code=404, detail="结算记录不存在")
    
    await db.delete(settlement)
    await db.commit()
    
    await service.refresh_contract_status(contract_id)
    return {"message": "删除成功"}
