"""
Expense Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.expense import ExpenseNonContract
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse
)
from app.services.auth import get_current_active_user, require_role

router = APIRouter()


@router.get("/", response_model=ExpenseListResponse)
async def list_expenses(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List expenses with pagination and filtering"""
    query = select(ExpenseNonContract)
    
    if keyword:
        # Removed payee_name from search as it's not in the new Requirement 3.4
        query = query.where(
            (ExpenseNonContract.expense_code.ilike(f"%{keyword}%")) | 
            (ExpenseNonContract.description.ilike(f"%{keyword}%")) |
            (ExpenseNonContract.handler.ilike(f"%{keyword}%")) |
            (ExpenseNonContract.responsible_person.ilike(f"%{keyword}%"))
        )
    
    if category:
        query = query.where(ExpenseNonContract.category == category)
        
    if status:
        query = query.where(ExpenseNonContract.status == status)
        
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
    return expense


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expense details"""
    result = await db.execute(select(ExpenseNonContract).where(ExpenseNonContract.id == expense_id))
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
