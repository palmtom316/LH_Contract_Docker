"""
Upstream Contract Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile
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
from app.services.status_service import calculate_contract_status
from sqlalchemy.orm import selectinload

router = APIRouter()

async def refresh_contract_status(db: AsyncSession, contract_id: int):
    """Recalculate and update contract status based on latest data"""
    query = select(ContractUpstream).options(
        selectinload(ContractUpstream.settlements),
        selectinload(ContractUpstream.receipts),
        selectinload(ContractUpstream.receivables),
    ).where(ContractUpstream.id == contract_id)
    
    result = await db.execute(query)
    contract = result.scalar_one_or_none()
    
    if not contract:
        return

    # Calculate Totals
    total_settlement = sum(s.settlement_amount or 0 for s in contract.settlements)
    total_received = sum(r.amount or 0 for r in contract.receipts)
    total_receivable = sum(r.amount or 0 for r in contract.receivables)
    
    new_status = calculate_contract_status(contract, total_settlement, total_received, total_receivable)
    
    if contract.status != new_status:
        contract.status = new_status
        db.add(contract)
        await db.commit()


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
        # Check if keyword is a number (could be contract ID)
        conditions = [
            ContractUpstream.contract_name.ilike(f"%{keyword}%"),
            ContractUpstream.contract_code.ilike(f"%{keyword}%"),
            ContractUpstream.party_a_name.ilike(f"%{keyword}%"),
            ContractUpstream.party_b_name.ilike(f"%{keyword}%")
        ]
        # If keyword is numeric, also search by ID
        if keyword.isdigit():
            conditions.append(ContractUpstream.id == int(keyword))
        
        from sqlalchemy import or_
        query = query.where(or_(*conditions))
    
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


@router.get("/export/excel")
async def export_contracts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export contracts to Excel"""
    try:
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
                "合同序号": c.id,
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/", response_model=ContractUpstreamResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_in: ContractUpstreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new upstream contract"""
    try:
        # Check unique ID (合同序号)
        existing_id = await db.execute(select(ContractUpstream).where(ContractUpstream.id == contract_in.id))
        if existing_id.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"合同序号 {contract_in.id} 已存在")
        
        # Check unique code
        existing = await db.execute(select(ContractUpstream).where(ContractUpstream.contract_code == contract_in.contract_code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="合同编号已存在")
            
        contract = ContractUpstream(**contract_in.model_dump(), created_by=current_user.id)
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(f"Create Contract Error: {str(e)}\n")
            f.write(traceback.format_exc())
            f.write("\n" + "-"*30 + "\n")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


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
    
    # Check id (contract serial number) uniqueness if it's being updated
    if 'id' in update_data and update_data['id'] != contract.id:
        existing_id = await db.execute(
            select(ContractUpstream).where(ContractUpstream.id == update_data['id'])
        )
        if existing_id.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"合同序号 {update_data['id']} 已存在")
    
    # Check contract_code uniqueness if it's being updated
    if 'contract_code' in update_data and update_data['contract_code'] != contract.contract_code:
        existing = await db.execute(
            select(ContractUpstream).where(
                ContractUpstream.contract_code == update_data['contract_code'],
                ContractUpstream.id != contract_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="合同编号已存在")
    
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
    await refresh_contract_status(db, contract_id)
    return receivable


@router.get("/{contract_id}/receivables", response_model=List[ReceivableResponse])
async def list_receivables(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceivable).where(FinanceUpstreamReceivable.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/receivables/{receivable_id}", response_model=ReceivableResponse)
async def update_receivable(
    contract_id: int,
    receivable_id: int,
    receivable_in: ReceivableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceivable).where(
        FinanceUpstreamReceivable.id == receivable_id,
        FinanceUpstreamReceivable.contract_id == contract_id
    )
    result = await db.execute(query)
    receivable = result.scalar_one_or_none()
    if not receivable:
        raise HTTPException(status_code=404, detail="应收款记录不存在")
    
    for key, value in receivable_in.model_dump(exclude={'contract_id'}).items():
        setattr(receivable, key, value)
    await db.commit()
    await db.refresh(receivable)
    await refresh_contract_status(db, contract_id)
    return receivable


@router.delete("/{contract_id}/receivables/{receivable_id}")
async def delete_receivable(
    contract_id: int,
    receivable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceivable).where(
        FinanceUpstreamReceivable.id == receivable_id,
        FinanceUpstreamReceivable.contract_id == contract_id
    )
    result = await db.execute(query)
    receivable = result.scalar_one_or_none()
    if not receivable:
        raise HTTPException(status_code=404, detail="应收款记录不存在")
    
    await db.delete(receivable)
    await db.commit()
    await refresh_contract_status(db, contract_id)
    return {"message": "删除成功"}


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


@router.put("/{contract_id}/invoices/{invoice_id}", response_model=InvoiceUpstreamResponse)
async def update_invoice(
    contract_id: int,
    invoice_id: int,
    invoice_in: InvoiceUpstreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamInvoice).where(
        FinanceUpstreamInvoice.id == invoice_id,
        FinanceUpstreamInvoice.contract_id == contract_id
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
    query = select(FinanceUpstreamInvoice).where(
        FinanceUpstreamInvoice.id == invoice_id,
        FinanceUpstreamInvoice.contract_id == contract_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票记录不存在")
    
    await db.delete(invoice)
    await db.commit()
    return {"message": "删除成功"}


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
    await refresh_contract_status(db, contract_id)
    return receipt


@router.get("/{contract_id}/receipts", response_model=List[ReceiptResponse])
async def list_receipts(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceipt).where(FinanceUpstreamReceipt.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    contract_id: int,
    receipt_id: int,
    receipt_in: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceipt).where(
        FinanceUpstreamReceipt.id == receipt_id,
        FinanceUpstreamReceipt.contract_id == contract_id
    )
    result = await db.execute(query)
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="回款记录不存在")
    
    for key, value in receipt_in.model_dump(exclude={'contract_id'}).items():
        setattr(receipt, key, value)
    await db.commit()
    await db.refresh(receipt)
    await refresh_contract_status(db, contract_id)
    return receipt


@router.delete("/{contract_id}/receipts/{receipt_id}")
async def delete_receipt(
    contract_id: int,
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(FinanceUpstreamReceipt).where(
        FinanceUpstreamReceipt.id == receipt_id,
        FinanceUpstreamReceipt.contract_id == contract_id
    )
    result = await db.execute(query)
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="回款记录不存在")
    
    await db.delete(receipt)
    await db.commit()
    await refresh_contract_status(db, contract_id)
    return {"message": "删除成功"}


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
    await refresh_contract_status(db, contract_id)
    return settlement


@router.get("/{contract_id}/settlements", response_model=List[SettlementResponse])
async def list_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(ProjectSettlement).where(ProjectSettlement.contract_id == contract_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{contract_id}/settlements/{settlement_id}", response_model=SettlementResponse)
async def update_settlement(
    contract_id: int,
    settlement_id: int,
    settlement_in: SettlementCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(ProjectSettlement).where(
        ProjectSettlement.id == settlement_id,
        ProjectSettlement.contract_id == contract_id
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
    query = select(ProjectSettlement).where(
        ProjectSettlement.id == settlement_id,
        ProjectSettlement.contract_id == contract_id
    )
    result = await db.execute(query)
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise HTTPException(status_code=404, detail="结算记录不存在")
    
    await db.delete(settlement)
    await db.commit()
    await refresh_contract_status(db, contract_id)
    return {"message": "删除成功"}


@router.get("/template/excel")
async def download_import_template():
    """Download Excel template for batch import"""
    # Create template DataFrame with column headers
    template_data = {
        "合同编号": ["HT-2024-001 (示例)"],
        "合同名称": ["XX工程施工合同 (示例)"],
        "甲方单位": ["XX电力公司 (示例)"],
        "乙方单位": ["重庆蓝海电气 (示例)"],
        "合同类别": ["总包合同"],
        "公司分类": ["市区配网"],
        "计价模式": ["总价包干"],
        "管理模式": ["自营"],
        "负责人": ["张三 (示例)"],
        "合同金额": [100000.00],
        "签约日期": ["2024-01-01"],
        "状态": ["进行中"],
        "备注": ["可选填写"]
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file
    filename = "upstream_contracts_import_template.xlsx"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Write to Excel with column width adjustment
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='合同数据')
        
        # Add a notes sheet
        notes_data = {
            "字段名称": ["合同编号", "合同名称", "甲方单位", "乙方单位", "合同类别", "公司分类", "计价模式", "管理模式", "负责人", "合同金额", "签约日期", "状态", "备注"],
            "是否必填": ["是", "是", "是", "是", "否", "否", "否", "否", "否", "是", "否", "否", "否"],
            "说明": [
                "唯一标识，不可重复",
                "合同的完整名称",
                "甲方公司全称",
                "乙方公司全称",
                "可选值: 总包合同/专业分包/劳务分包/技术服务/运营维护/物资采购/其他合同",
                "可选值: 市区配网/市北配网/用户工程/维护工程/变电工程/营销工程/北源工程/安驰工程",
                "可选值: 总价包干/单价包干/工日单价/费率下浮",
                "可选值: 自营/合作/挂靠",
                "项目负责人姓名",
                "数字，支持小数",
                "格式: YYYY-MM-DD",
                "可选值: 进行中/已完成/已终止",
                "其他补充信息"
            ]
        }
        notes_df = pd.DataFrame(notes_data)
        notes_df.to_excel(writer, index=False, sheet_name='填写说明')
    
    return FileResponse(
        path=filepath, 
        filename=filename, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.post("/import/excel")
async def import_contracts_from_excel(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Batch import upstream contracts from Excel file"""
    # Check file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持 Excel 文件格式 (.xlsx, .xls)")
    
    try:
        # Read Excel file
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
        
        # Validate required columns
        required_columns = ["合同编号", "合同名称", "甲方单位", "乙方单位", "合同金额"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"缺少必填列: {', '.join(missing_columns)}")
        
        # Process each row
        success_count = 0
        error_rows = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (1-indexed + header)
            
            try:
                # Check if contract_code already exists
                contract_code = str(row.get("合同编号", "")).strip()
                if not contract_code or "(示例)" in contract_code:
                    continue  # Skip empty or example rows
                    
                existing = await db.execute(
                    select(ContractUpstream).where(ContractUpstream.contract_code == contract_code)
                )
                if existing.scalar_one_or_none():
                    error_rows.append({"row": row_num, "error": f"合同编号 '{contract_code}' 已存在"})
                    continue
                
                # Parse sign_date
                sign_date_val = row.get("签约日期")
                sign_date = None
                if pd.notna(sign_date_val):
                    if isinstance(sign_date_val, str):
                        try:
                            sign_date = datetime.strptime(sign_date_val.strip(), "%Y-%m-%d").date()
                        except ValueError:
                            sign_date = None
                    elif hasattr(sign_date_val, 'date'):
                        sign_date = sign_date_val.date() if callable(getattr(sign_date_val, 'date', None)) else sign_date_val
                    elif isinstance(sign_date_val, date):
                        sign_date = sign_date_val
                
                # Parse contract amount
                amount_val = row.get("合同金额", 0)
                contract_amount = 0
                if pd.notna(amount_val):
                    try:
                        contract_amount = float(amount_val)
                    except (ValueError, TypeError):
                        contract_amount = 0
                
                # Map category to enum
                category_str = str(row.get("合同类别", "")).strip() or None
                pricing_mode_str = str(row.get("计价模式", "")).strip() or None
                management_mode_str = str(row.get("管理模式", "")).strip() or None
                
                # Create contract
                contract = ContractUpstream(
                    contract_code=contract_code,
                    contract_name=str(row.get("合同名称", "")).strip(),
                    party_a_name=str(row.get("甲方单位", "")).strip(),
                    party_b_name=str(row.get("乙方单位", "")).strip(),
                    category=category_str,
                    company_category=str(row.get("公司分类", "")).strip() or None,
                    pricing_mode=pricing_mode_str,
                    management_mode=management_mode_str,
                    responsible_person=str(row.get("负责人", "")).strip() or None,
                    contract_amount=contract_amount,
                    sign_date=sign_date,
                    status=str(row.get("状态", "进行中")).strip() or "进行中",
                    notes=str(row.get("备注", "")).strip() or None,
                    created_by=current_user.id
                )
                
                db.add(contract)
                success_count += 1
                
            except Exception as e:
                error_rows.append({"row": row_num, "error": str(e)})
        
        # Commit all successful inserts
        if success_count > 0:
            await db.commit()
        
        return {
            "message": f"导入完成",
            "success_count": success_count,
            "error_count": len(error_rows),
            "errors": error_rows[:20]  # Return first 20 errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")




