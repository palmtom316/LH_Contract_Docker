"""
Management Contract Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime

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

router = APIRouter()


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
    return payable


@router.get("/{contract_id}/payables", response_model=List[ManagementPayableResponse])
async def list_payables(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayable).where(FinanceManagementPayable.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


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
    return payment


@router.get("/{contract_id}/payments", response_model=List[ManagementPaymentResponse])
async def list_payments(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceManagementPayment).where(FinanceManagementPayment.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


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
    return settlement
