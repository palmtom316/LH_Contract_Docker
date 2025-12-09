"""
Upstream Contract Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import date, datetime
import pandas as pd
import io
import os
from app.config import settings

from app.database import get_db
from app.models.user import User
from app.models.contract_upstream import (
    ContractUpstream, FinanceUpstreamReceivable, FinanceUpstreamInvoice,
    FinanceUpstreamReceipt, ProjectSettlement
)
# We import Enums for type checking or specific logic if needed
from app.models.enums import ContractCategory, PaymentCategory

from app.schemas.contract_upstream import (
    ContractUpstreamCreate, ContractUpstreamUpdate, ContractUpstreamResponse, ContractUpstreamListResponse,
    ReceivableCreate, ReceivableResponse,
    InvoiceUpstreamCreate, InvoiceUpstreamResponse,
    ReceiptCreate, ReceiptResponse,
    SettlementCreate, SettlementResponse
)
from app.services.auth import get_current_active_user

router = APIRouter()


# ===== Contract Operations =====

@router.get("/", response_model=ContractUpstreamListResponse)
async def list_contracts(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List upstream contracts with pagination and filtering"""
    query = select(ContractUpstream)
    
    if keyword:
        query = query.where(
            (ContractUpstream.contract_name.ilike(f"%{keyword}%")) | 
            (ContractUpstream.contract_code.ilike(f"%{keyword}%")) |
            (ContractUpstream.party_a_name.ilike(f"%{keyword}%")) |
            (ContractUpstream.party_b_name.ilike(f"%{keyword}%"))
        )
    
    if status:
        query = query.where(ContractUpstream.status == status)
        
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    
    # Pagination
    query = query.order_by(desc(ContractUpstream.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    return {
        "items": contracts,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=ContractUpstreamResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractUpstreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new upstream contract"""
    # Check unique code
    existing = await db.execute(select(ContractUpstream).where(ContractUpstream.contract_code == contract_in.contract_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="合同编号已存在")
        
    contract = ContractUpstream(**contract_in.model_dump(), created_by=current_user.id)
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


@router.get("/{contract_id}", response_model=ContractUpstreamResponse)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contract details"""
    result = await db.execute(select(ContractUpstream).where(ContractUpstream.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
        
    return contract


@router.get("/{contract_id}/summary")
async def get_contract_summary(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get read-only summary for downstream linking"""
    result = await db.execute(select(ContractUpstream).where(ContractUpstream.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
        
    return {
        "id": contract.id,
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name,
        "contract_amount": contract.contract_amount,
        "party_a_name": contract.party_a_name,
        "project_name": contract.project_name
    }


@router.put("/{contract_id}", response_model=ContractUpstreamResponse)
async def update_contract(
    contract_id: int,
    contract_in: ContractUpstreamUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update contract"""
    result = await db.execute(select(ContractUpstream).where(ContractUpstream.id == contract_id))
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
    result = await db.execute(select(ContractUpstream).where(ContractUpstream.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
        
    await db.delete(contract)
    await db.commit()
    return {"message": "合同已删除"}


# ===== Sub-resource Operations =====

# 1. Receivables (应收款)
@router.post("/{contract_id}/receivables", response_model=ReceivableResponse)
async def create_receivable(
    contract_id: int,
    receivable_in: ReceivableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != receivable_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    receivable = FinanceUpstreamReceivable(**receivable_in.model_dump())
    db.add(receivable)
    await db.commit()
    await db.refresh(receivable)
    return receivable


@router.get("/{contract_id}/receivables", response_model=List[ReceivableResponse])
async def list_receivables(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceivable).where(FinanceUpstreamReceivable.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


# 2. Invoices (开票)
@router.post("/{contract_id}/invoices", response_model=InvoiceUpstreamResponse)
async def create_invoice(
    contract_id: int,
    invoice_in: InvoiceUpstreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != invoice_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    invoice = FinanceUpstreamInvoice(**invoice_in.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/{contract_id}/invoices", response_model=List[InvoiceUpstreamResponse])
async def list_invoices(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamInvoice).where(FinanceUpstreamInvoice.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


# 3. Receipts (收款)
@router.post("/{contract_id}/receipts", response_model=ReceiptResponse)
async def create_receipt(
    contract_id: int,
    receipt_in: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != receipt_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    receipt = FinanceUpstreamReceipt(**receipt_in.model_dump())
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@router.get("/{contract_id}/receipts", response_model=List[ReceiptResponse])
async def list_receipts(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceipt).where(FinanceUpstreamReceipt.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


# 4. Settlements (结算)
@router.post("/{contract_id}/settlements", response_model=SettlementResponse)
async def create_settlement(
    contract_id: int,
    settlement_in: SettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if contract_id != settlement_in.contract_id:
        raise HTTPException(status_code=400, detail="合同ID不匹配")
        
    settlement = ProjectSettlement(**settlement_in.model_dump())
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    return settlement


@router.get("/{contract_id}/settlements", response_model=List[SettlementResponse])
async def list_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(ProjectSettlement).where(ProjectSettlement.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/export/excel")
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export contracts to Excel"""
    # 1. Query Data
    query = select(ContractUpstream)
    
    if keyword:
        query = query.where(
            (ContractUpstream.contract_name.ilike(f"%{keyword}%")) | 
            (ContractUpstream.contract_code.ilike(f"%{keyword}%")) |
            (ContractUpstream.party_a_name.ilike(f"%{keyword}%")) |
            (ContractUpstream.party_b_name.ilike(f"%{keyword}%"))
        )
    
    if status:
        query = query.where(ContractUpstream.status == status)
        
    query = query.order_by(desc(ContractUpstream.created_at))
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    # 2. Convert to DataFrame
    data = []
    for c in contracts:
        data.append({
            "合同编号": c.contract_code,
            "合同名称": c.contract_name,
            "甲方单位": c.party_a_name,
            "乙方单位": c.party_b_name,
            "合同类别": c.category.value if hasattr(c.category, 'value') else c.category,
            "公司分类": c.company_category,
            "计价模式": c.pricing_mode.value if hasattr(c.pricing_mode, 'value') else c.pricing_mode,
            "管理模式": c.management_mode.value if hasattr(c.management_mode, 'value') else c.management_mode,
            "负责人": c.responsible_person,
            "合同金额": float(c.contract_amount) if c.contract_amount else 0,
            "签约日期": c.sign_date,
            "状态": c.status,
            "备注": c.notes
        })
        
    df = pd.DataFrame(data)
    
    # 3. Create Excel file
    filename = f"contracts_upstream_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Ensure directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Write to Excel
    df.to_excel(filepath, index=False, engine='openpyxl')
    
    # 4. Return file
    return FileResponse(
        path=filepath, 
        filename=filename, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
