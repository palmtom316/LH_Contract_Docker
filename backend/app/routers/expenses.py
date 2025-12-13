"""
Expense Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io
import urllib.parse

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse
)
from app.services.auth import get_current_active_user, require_role
from app.services.expense_service import ExpenseService

router = APIRouter()

# Dependency
def get_expense_service(db: AsyncSession = Depends(get_db)) -> ExpenseService:
    return ExpenseService(db)

@router.get("/export/excel", response_class=StreamingResponse)
async def export_expenses(
    keyword: Optional[str] = None,
    attribution: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    upstream_contract_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    service: ExpenseService = Depends(get_expense_service)
):
    """Export expenses to Excel"""
    try:
        expenses = await service.list_all_expenses(
            keyword, attribution, category, start_date, end_date, upstream_contract_id
        )
        
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
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    keyword: Optional[str] = None,
    attribution: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    upstream_contract_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    service: ExpenseService = Depends(get_expense_service)
):
    """List expenses with pagination and filtering"""
    return await service.list_expenses(
        page, page_size, keyword, attribution, category, start_date, end_date, upstream_contract_id
    )


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_in: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    service: ExpenseService = Depends(get_expense_service)
):
    """Create new expense"""
    return await service.create_expense(expense_in, current_user.id)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ExpenseService = Depends(get_expense_service)
):
    """Get expense details"""
    expense = await service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="费用记录不存在")
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ExpenseService = Depends(get_expense_service)
):
    """Update expense"""
    return await service.update_expense(expense_id, expense_in, current_user.id)


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ExpenseService = Depends(get_expense_service)
):
    """Delete expense"""
    await service.delete_expense(expense_id)
    return {"message": "费用记录已删除"}


@router.post("/{expense_id}/approve")
async def approve_expense(
    expense_id: int,
    approved: bool = True,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER])),
    service: ExpenseService = Depends(get_expense_service)
):
    """Approve or reject expense"""
    await service.approve_expense(expense_id, approved, current_user.id)
    return {"message": f"费用已{'审核通过' if approved else '驳回'}"}
