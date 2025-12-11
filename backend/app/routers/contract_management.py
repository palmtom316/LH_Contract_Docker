"""
Management Contract Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
import urllib.parse

from app.database import get_db
from app.models.user import User
from app.models.contract_management import (
    ContractManagement, FinanceManagementPayable, FinanceManagementInvoice,
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
from app.services.status_service import calculate_contract_status
from sqlalchemy.orm import selectinload

router = APIRouter()

async def refresh_contract_status(db: AsyncSession, contract_id: int):
    """Recalculate and update contract status based on latest data"""
    query = select(ContractManagement).options(
        selectinload(ContractManagement.settlements),
        selectinload(ContractManagement.payments),
        selectinload(ContractManagement.payables),
    ).where(ContractManagement.id == contract_id)
    
    result = await db.execute(query)
    contract = result.scalar_one_or_none()
    
    if not contract:
        return

    # Calculate Totals
    total_settlement = sum(s.settlement_amount or 0 for s in contract.settlements)
    total_paid = sum(p.amount or 0 for p in contract.payments)
    total_payable = sum(p.amount or 0 for p in contract.payables)
    
    new_status = calculate_contract_status(contract, total_settlement, total_paid, total_payable)
    
    if contract.status != new_status:
        contract.status = new_status
        db.add(contract)
        await db.commit()

@router.get("/export/excel", response_class=StreamingResponse)
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export management contracts to Excel"""
    try:
        query = select(ContractManagement)
        
        if keyword:
            query = query.where(
                (ContractManagement.contract_name.ilike(f"%{keyword}%")) | 
                (ContractManagement.contract_code.ilike(f"%{keyword}%")) |
                (ContractManagement.party_a_name.ilike(f"%{keyword}%")) |
                (ContractManagement.party_b_name.ilike(f"%{keyword}%"))
            )
        
        if status:
            query = query.where(ContractManagement.status == status)
            
        query = query.order_by(desc(ContractManagement.created_at))
        result = await db.execute(query)
        contracts = result.scalars().all()
        
        # Create DataFrame
        data = []
        for c in contracts:
            data.append({
                "合同序号": c.id,
                "合同编号": c.contract_code,
                "合同名称": c.contract_name,
                "甲方": c.party_a_name,
                "乙方": c.party_b_name,
                "合同类别": c.category.value if hasattr(c.category, 'value') else c.category,
                "计价模式": c.pricing_mode.value if hasattr(c.pricing_mode, 'value') else c.pricing_mode,
                "合同金额": float(c.contract_amount),
                "签订日期": c.sign_date,
                "状态": c.status
            })
            
        df = pd.DataFrame(data)
        
        # Save to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Contracts')
        output.seek(0)
        
        filename = f"管理合同列表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ===== Contract Operations =====

@router.get("/", response_model=ContractManagementListResponse)
async def list_contracts(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List management contracts with pagination and filtering"""
    query = select(ContractManagement)
    
    if keyword:
        query = query.where(
            (ContractManagement.contract_name.ilike(f"%{keyword}%")) | 
            (ContractManagement.contract_code.ilike(f"%{keyword}%")) |
            (ContractManagement.party_a_name.ilike(f"%{keyword}%")) |
            (ContractManagement.party_b_name.ilike(f"%{keyword}%"))
        )
    
    if status:
        query = query.where(ContractManagement.status == status)
        
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    
    # Pagination
    query = query.order_by(desc(ContractManagement.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    return {
        "items": contracts,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=ContractManagementResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractManagementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new management contract"""
    existing = await db.execute(select(ContractManagement).where(ContractManagement.contract_code == contract_in.contract_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="合同编号已存在")
        
    contract = ContractManagement(**contract_in.model_dump(), created_by=current_user.id)
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    await refresh_contract_status(db, contract.id)
    return contract


@router.get("/{contract_id}", response_model=ContractManagementResponse)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contract details"""
    result = await db.execute(select(ContractManagement).where(ContractManagement.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.put("/{contract_id}", response_model=ContractManagementResponse)
async def update_contract(
    contract_id: int,
    contract_in: ContractManagementUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update contract"""
    result = await db.execute(select(ContractManagement).where(ContractManagement.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
        
    update_data = contract_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
        
    await db.commit()
    await db.refresh(contract)
    await refresh_contract_status(db, contract.id)
    return contract


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete contract"""
    result = await db.execute(select(ContractManagement).where(ContractManagement.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
        
    await db.delete(contract)
    await db.commit()
    return {"message": "合同已删除"}


# ===== Sub-resource Operations =====

# 1. Payables (应付款)
@router.post("/{contract_id}/payables", response_model=ManagementPayableResponse)
async def create_payable(
    contract_id: int,
    payable_in: ManagementPayableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != payable_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    payable = FinanceManagementPayable(**payable_in.model_dump())
    db.add(payable)
    await db.commit()
    await db.refresh(payable)
    await refresh_contract_status(db, contract_id)
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
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayable).where(
        FinanceManagementPayable.id == payable_id,
        FinanceManagementPayable.contract_id == contract_id
    )
    result = await db.execute(query)
    payable = result.scalar_one_or_none()
    if not payable:
        raise HTTPException(status_code=404, detail="应付款记录不存在")
    
    for key, value in payable_in.model_dump(exclude={'contract_id'}).items():
        setattr(payable, key, value)
    await db.commit()
    await db.refresh(payable)
    await refresh_contract_status(db, contract_id)
    return payable


@router.delete("/{contract_id}/payables/{payable_id}")
async def delete_payable(
    contract_id: int,
    payable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayable).where(
        FinanceManagementPayable.id == payable_id,
        FinanceManagementPayable.contract_id == contract_id
    )
    result = await db.execute(query)
    payable = result.scalar_one_or_none()
    if not payable:
        raise HTTPException(status_code=404, detail="应付款记录不存在")
    
    await db.delete(payable)
    await db.commit()
    await refresh_contract_status(db, contract_id)
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
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
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
        raise HTTPException(status_code=404, detail="发票记录不存在")
    
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
        raise HTTPException(status_code=404, detail="发票记录不存在")
    
    await db.delete(invoice)
    await db.commit()
    return {"message": "删除成功"}


# 3. Payments (付款)
@router.post("/{contract_id}/payments", response_model=ManagementPaymentResponse)
async def create_payment(
    contract_id: int,
    payment_in: ManagementPaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != payment_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    payment = FinanceManagementPayment(**payment_in.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    await refresh_contract_status(db, contract_id)
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
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayment).where(
        FinanceManagementPayment.id == payment_id,
        FinanceManagementPayment.contract_id == contract_id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="付款记录不存在")
    
    for key, value in payment_in.model_dump(exclude={'contract_id'}).items():
        setattr(payment, key, value)
    await db.commit()
    await db.refresh(payment)
    await refresh_contract_status(db, contract_id)
    return payment


@router.delete("/{contract_id}/payments/{payment_id}")
async def delete_payment(
    contract_id: int,
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayment).where(
        FinanceManagementPayment.id == payment_id,
        FinanceManagementPayment.contract_id == contract_id
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="付款记录不存在")
    
    await db.delete(payment)
    await db.commit()
    await refresh_contract_status(db, contract_id)
    return {"message": "删除成功"}


# 4. Settlements (结算)
@router.post("/{contract_id}/settlements", response_model=ManagementSettlementResponse)
async def create_settlement(
    contract_id: int,
    settlement_in: ManagementSettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != settlement_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    settlement = ManagementSettlement(**settlement_in.model_dump())
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    await refresh_contract_status(db, contract_id)
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
    db: AsyncSession = Depends(get_db)
):
    query = select(ManagementSettlement).where(
        ManagementSettlement.id == settlement_id,
        ManagementSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise HTTPException(status_code=404, detail="结算记录不存在")
    
    for key, value in settlement_in.model_dump(exclude={'contract_id'}).items():
        setattr(settlement, key, value)
    await db.commit()
    await db.refresh(settlement)
    await refresh_contract_status(db, contract_id)
    return settlement


@router.delete("/{contract_id}/settlements/{settlement_id}")
async def delete_settlement(
    contract_id: int,
    settlement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(ManagementSettlement).where(
        ManagementSettlement.id == settlement_id,
        ManagementSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise HTTPException(status_code=404, detail="结算记录不存在")
    
    await db.delete(settlement)
    await db.commit()
    await refresh_contract_status(db, contract_id)
    return {"message": "删除成功"}
