from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.expense import ExpenseNonContract
from app.models.user import User, UserRole
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.cache import cache, dashboard_cache_key
from app.services.audit_service import create_audit_log, AuditAction, ResourceType
from app.models.enums import ExpenseCategory, ExpenseType

class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _invalidate_dashboard_cache(self):
        """Clear dashboard cache when data changes"""
        await cache.delete(dashboard_cache_key())

    async def get_expense(self, expense_id: int) -> Optional[ExpenseNonContract]:
        """Get expense by ID"""
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
        category: Optional[str] = None,
        expense_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        upstream_contract_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """List expenses with filtering and pagination"""
        query = select(ExpenseNonContract).options(
            joinedload(ExpenseNonContract.upstream_contract)
        )

        if keyword:
            conditions = [
                ExpenseNonContract.expense_code.ilike(f"%{keyword}%"),
                ExpenseNonContract.description.ilike(f"%{keyword}%")
            ]
            query = query.where(or_(*conditions))
        
        if category:
            # Support both English Key and Chinese Value
            search_vals = [category]
            for item in ExpenseCategory:
                if item.value == category:
                    search_vals.append(item.name)
                    break
            query = query.where(ExpenseNonContract.category.in_(search_vals))
            
        if expense_type:
            # Support both English Key and Chinese Value
            search_vals = [expense_type]
            for item in ExpenseType:
                if item.value == expense_type:
                    search_vals.append(item.name)
                    break
            query = query.where(ExpenseNonContract.expense_type.in_(search_vals))
            
        if upstream_contract_id:
            query = query.where(ExpenseNonContract.upstream_contract_id == upstream_contract_id)

        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.where(ExpenseNonContract.expense_date >= sd)
            except ValueError:
                pass
        
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.where(ExpenseNonContract.expense_date <= ed)
            except ValueError:
                pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Pagination
        query = query.order_by(desc(ExpenseNonContract.created_at)).offset((page - 1) * page_size).limit(page_size)
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
        category: Optional[str] = None,
        expense_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        upstream_contract_id: Optional[int] = None
    ) -> List[ExpenseNonContract]:
        """List all expenses for export"""
        query = select(ExpenseNonContract).options(
            joinedload(ExpenseNonContract.upstream_contract)
        )
        
        if keyword:
            conditions = [
                ExpenseNonContract.expense_code.ilike(f"%{keyword}%"),
                ExpenseNonContract.description.ilike(f"%{keyword}%")
            ]
            query = query.where(or_(*conditions))
        
        if category:
            # Support both English Key and Chinese Value
            search_vals = [category]
            for item in ExpenseCategory:
                if item.value == category:
                    search_vals.append(item.name)
                    break
            query = query.where(ExpenseNonContract.category.in_(search_vals))
            
        if expense_type:
            # Support both English Key and Chinese Value
            search_vals = [expense_type]
            for item in ExpenseType:
                if item.value == expense_type:
                    search_vals.append(item.name)
                    break
            query = query.where(ExpenseNonContract.expense_type.in_(search_vals))
            
        if upstream_contract_id:
            query = query.where(ExpenseNonContract.upstream_contract_id == upstream_contract_id)

        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.where(ExpenseNonContract.expense_date >= sd)
            except ValueError:
                pass
        
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.where(ExpenseNonContract.expense_date <= ed)
            except ValueError:
                pass

        query = query.order_by(desc(ExpenseNonContract.created_at))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_expense(self, expense_in: ExpenseCreate, user: User) -> ExpenseNonContract:
        """Create new expense"""
        existing = await self.db.execute(select(ExpenseNonContract).where(ExpenseNonContract.expense_code == expense_in.expense_code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="费用编号已存在")
            
        expense = ExpenseNonContract(**expense_in.model_dump(), created_by=user.id, updated_by=user.id)
        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)
        
        await self._invalidate_dashboard_cache()

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.CREATE,
            resource_type=ResourceType.EXPENSE,
            resource_id=expense.id,
            resource_name=expense.expense_code,
            new_values=expense_in.model_dump(mode='json'),
            description=f"创建无合同费用: {expense.expense_code}"
        )
        
        # Return with relationship
        return await self.get_expense(expense.id)

    async def update_expense(self, expense_id: int, expense_in: ExpenseUpdate, user: User) -> ExpenseNonContract:
        """Update existing expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")

        # 检查费用编号是否更新且是否与其他记录重复
        update_data = expense_in.model_dump(exclude_unset=True)
        if 'expense_code' in update_data and update_data['expense_code'] != expense.expense_code:
            existing = await self.db.execute(
                select(ExpenseNonContract).where(
                    ExpenseNonContract.expense_code == update_data['expense_code'],
                    ExpenseNonContract.id != expense_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="费用编号已存在")

        old_values = {
            k: getattr(expense, k) for k in update_data.keys() 
            if hasattr(expense, k)
        }

        for field, value in update_data.items():
            setattr(expense, field, value)
        expense.updated_by = user.id
            
        await self.db.commit()
        await self.db.refresh(expense)
        
        await self._invalidate_dashboard_cache()

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.UPDATE,
            resource_type=ResourceType.EXPENSE,
            resource_id=expense.id,
            resource_name=expense.expense_code,
            old_values=old_values,
            new_values=update_data,
            description=f"更新无合同费用: {expense.expense_code}"
        )

        return expense

    async def delete_expense(self, expense_id: int, user: User) -> None:
        """Delete expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
        
        expense_code = expense.expense_code
        expense_data = {
            "id": expense.id,
            "expense_code": expense.expense_code,
            "description": expense.description
        }
            
        await self.db.delete(expense)
        await self.db.commit()
        
        await self._invalidate_dashboard_cache()

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.DELETE,
            resource_type=ResourceType.EXPENSE,
            resource_id=expense_id,
            resource_name=expense_code,
            old_values=expense_data,
            description=f"删除无合同费用: {expense_code}"
        )

    async def approve_expense(self, expense_id: int, approved: bool, user: User) -> None:
        """Approve or reject expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
            
        expense.status = "已审核" if approved else "已驳回"
        expense.approved_by = user.id
        expense.approved_at = datetime.utcnow()
        
        await self.db.commit()
        await self._invalidate_dashboard_cache()

        # Audit Log
        action = AuditAction.APPROVE if approved else AuditAction.REJECT
        await create_audit_log(
            db=self.db,
            user=user,
            action=action,
            resource_type=ResourceType.EXPENSE,
            resource_id=expense.id,
            resource_name=expense.expense_code,
            description=f"{'审核通过' if approved else '驳回'}无合同费用: {expense.expense_code}"
        )
