"""
Expense Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime, date as date_type
import pandas as pd
import io
import urllib.parse

from app.database import get_db
from app.models.user import User, UserRole
from app.models.expense import ExpenseNonContract
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse
)
from app.services.auth import get_current_active_user, require_role

router = APIRouter()


@router.get("/export/excel", response_class=StreamingResponse)
async def export_expenses(
    keyword: Optional[str] = None,
    attribution: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    upstream_contract_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export expenses to Excel"""
    try:
        query = select(ExpenseNonContract).options(joinedload(ExpenseNonContract.upstream_contract))
        
        if keyword:
            query = query.where(
                (ExpenseNonContract.expense_code.ilike(f"%{keyword}%")) | 
                (ExpenseNonContract.description.ilike(f"%{keyword}%")) |
                (ExpenseNonContract.handler.ilike(f"%{keyword}%")) |
                (ExpenseNonContract.responsible_person.ilike(f"%{keyword}%"))
            )
        
        if attribution:
            query = query.where(ExpenseNonContract.attribution == attribution)
    
        if category:
            query = query.where(ExpenseNonContract.category == category)
            


        # Date range filter
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.where(ExpenseNonContract.expense_date >= start_date_obj)
            except ValueError:
                pass
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.where(ExpenseNonContract.expense_date <= end_date_obj)
            except ValueError:
                pass
        
        # Upstream contract ID filter
        if upstream_contract_id:
            query = query.where(ExpenseNonContract.upstream_contract_id == upstream_contract_id)
            
        query = query.order_by(desc(ExpenseNonContract.expense_date))
        result = await db.execute(query)
        expenses = result.scalars().all()
        
        # Create DataFrame
        data = []
        for e in expenses:
            data.append({
                "编号": e.expense_code,
                "日期": e.expense_date,
                "费用归属": e.attribution,
                "费用分类": e.category,
                "关联上游合同": e.upstream_contract.contract_name if e.upstream_contract else None,
                "说明": e.description,
                "金额": float(e.amount),
                "经办人": e.handler,
                "负责人": e.responsible_person
            })
            
        df = pd.DataFrame(data)
        
        # Save to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Expenses')
        output.seek(0)
        
        filename = f"费用列表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
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


@router.get("/", response_model=ExpenseListResponse)
async def list_expenses(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    attribution: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    upstream_contract_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List expenses with pagination and filtering"""
    query = select(ExpenseNonContract).options(joinedload(ExpenseNonContract.upstream_contract))
    
    if keyword:
        # Removed payee_name from search as it's not in the new Requirement 3.4
        query = query.where(
            (ExpenseNonContract.expense_code.ilike(f"%{keyword}%")) | 
            (ExpenseNonContract.description.ilike(f"%{keyword}%")) |
            (ExpenseNonContract.handler.ilike(f"%{keyword}%")) |
            (ExpenseNonContract.responsible_person.ilike(f"%{keyword}%"))
        )
    
    if attribution:
        query = query.where(ExpenseNonContract.attribution == attribution)

    if category:
        query = query.where(ExpenseNonContract.category == category)
        

    
    # Date range filter
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.where(ExpenseNonContract.expense_date >= start_date_obj)
        except ValueError:
            pass
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.where(ExpenseNonContract.expense_date <= end_date_obj)
        except ValueError:
            pass
    
    # Upstream contract ID filter
    if upstream_contract_id:
        query = query.where(ExpenseNonContract.upstream_contract_id == upstream_contract_id)
        
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    
    # Pagination
    query = query.order_by(desc(ExpenseNonContract.expense_date)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    expenses = result.scalars().all()
    
    return {
        "items": expenses,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_in: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new expense"""
    existing = await db.execute(select(ExpenseNonContract).where(ExpenseNonContract.expense_code == expense_in.expense_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="费用编号已存在")
        
    expense = ExpenseNonContract(**expense_in.model_dump(), created_by=current_user.id)
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    
    # Reload with relationship
    result = await db.execute(
        select(ExpenseNonContract)
        .options(joinedload(ExpenseNonContract.upstream_contract))
        .where(ExpenseNonContract.id == expense.id)
    )
    expense = result.scalar_one()
    return expense


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expense details"""
    result = await db.execute(
        select(ExpenseNonContract)
        .options(joinedload(ExpenseNonContract.upstream_contract))
        .where(ExpenseNonContract.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="费用记录不存在")
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update expense"""
    result = await db.execute(select(ExpenseNonContract).where(ExpenseNonContract.id == expense_id))
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="费用记录不存在")
        
    update_data = expense_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)
        
    await db.commit()
    await db.refresh(expense)
    
    # Reload with relationship
    result = await db.execute(
        select(ExpenseNonContract)
        .options(joinedload(ExpenseNonContract.upstream_contract))
        .where(ExpenseNonContract.id == expense.id)
    )
    expense = result.scalar_one()
    return expense


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete expense"""
    result = await db.execute(select(ExpenseNonContract).where(ExpenseNonContract.id == expense_id))
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="费用记录不存在")
        
    await db.delete(expense)
    await db.commit()
    return {"message": "费用记录已删除"}


@router.post("/{expense_id}/approve")
async def approve_expense(
    expense_id: int,
    approved: bool = True,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER])),
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject expense"""
    result = await db.execute(select(ExpenseNonContract).where(ExpenseNonContract.id == expense_id))
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(status_code=404, detail="费用记录不存在")
        
    expense.status = "已审核" if approved else "已驳回"
    expense.approved_by = current_user.id
    expense.approved_at = datetime.utcnow()
    
    await db.commit()
    return {"message": f"费用已{'审核通过' if approved else '驳回'}"}
