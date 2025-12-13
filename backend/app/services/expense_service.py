from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.expense import ExpenseNonContract
from app.models.user import UserRole
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.cache import cache, dashboard_cache_key

class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _invalidate_dashboard_cache(self):
        """Clear dashboard cache when expense data changes"""
        await cache.delete(dashboard_cache_key())

    async def get_expense(self, expense_id: int) -> Optional[ExpenseNonContract]:
        """Get expense by ID with upstream contract info"""
        query = select(ExpenseNonContract).options(
            joinedload(ExpenseNonContract.upstream_contract)
        ).where(ExpenseNonContract.id == expense_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_expenses(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        attribution: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        upstream_contract_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """List expenses with filtering and pagination"""
        query = select(ExpenseNonContract).options(joinedload(ExpenseNonContract.upstream_contract))

        if keyword:
            conditions = [
                ExpenseNonContract.expense_code.ilike(f"%{keyword}%"),
                ExpenseNonContract.description.ilike(f"%{keyword}%"),
                ExpenseNonContract.handler.ilike(f"%{keyword}%"),
                ExpenseNonContract.responsible_person.ilike(f"%{keyword}%")
            ]
            query = query.where(or_(*conditions))

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
        total = (await self.db.execute(count_query)).scalar_one()

        # Pagination
        query = query.order_by(desc(ExpenseNonContract.expense_date)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        expenses = result.scalars().all()

        return {
            "items": expenses,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def list_all_expenses(
        self,
        keyword: Optional[str] = None,
        attribution: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        upstream_contract_id: Optional[int] = None
    ) -> List[ExpenseNonContract]:
        """List all expenses for export (no pagination)"""
        query = select(ExpenseNonContract).options(joinedload(ExpenseNonContract.upstream_contract))
        
        if keyword:
            conditions = [
                ExpenseNonContract.expense_code.ilike(f"%{keyword}%"),
                ExpenseNonContract.description.ilike(f"%{keyword}%"),
                ExpenseNonContract.handler.ilike(f"%{keyword}%"),
                ExpenseNonContract.responsible_person.ilike(f"%{keyword}%")
            ]
            query = query.where(or_(*conditions))

        if attribution:
            query = query.where(ExpenseNonContract.attribution == attribution)

        if category:
            query = query.where(ExpenseNonContract.category == category)
            
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
        
        if upstream_contract_id:
            query = query.where(ExpenseNonContract.upstream_contract_id == upstream_contract_id)
            
        query = query.order_by(desc(ExpenseNonContract.expense_date))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_expense(self, expense_in: ExpenseCreate, user_id: int) -> ExpenseNonContract:
        """Create new expense"""
        existing = await self.db.execute(select(ExpenseNonContract).where(ExpenseNonContract.expense_code == expense_in.expense_code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="费用编号已存在")
            
        expense = ExpenseNonContract(**expense_in.model_dump(), created_by=user_id, updated_by=user_id)
        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)
        
        await self._invalidate_dashboard_cache()
        
        # Return with relationship
        return await self.get_expense(expense.id)

    async def update_expense(self, expense_id: int, expense_in: ExpenseUpdate, user_id: int) -> ExpenseNonContract:
        """Update existing expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")

        update_data = expense_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)
        expense.updated_by = user_id
            
        await self.db.commit()
        await self.db.refresh(expense)
        
        await self._invalidate_dashboard_cache()
        return expense

    async def delete_expense(self, expense_id: int) -> None:
        """Delete expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
            
        await self.db.delete(expense)
        await self.db.commit()
        
        await self._invalidate_dashboard_cache()

    async def approve_expense(self, expense_id: int, approved: bool, user_id: int) -> None:
        """Approve or reject expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
            
        expense.status = "已审核" if approved else "已驳回"
        expense.approved_by = user_id
        expense.approved_at = datetime.utcnow()
        
        await self.db.commit()
        await self._invalidate_dashboard_cache()
