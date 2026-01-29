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
from app.services.contract_code_generator import ContractCodeGenerator

class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _can_view_all_expenses(self, user: User) -> bool:
        """
        Check if user can view all expenses.
        ADMIN, CONTRACT_MANAGER, and FINANCE roles can view all data.
        Other roles (ENGINEERING, AUDIT, BIDDING, GENERAL_AFFAIRS) can only see their own data.
        """
        if user.is_superuser:
            return True
        return user.role in [
            UserRole.ADMIN,
            UserRole.CONTRACT_MANAGER,
            UserRole.FINANCE,
        ]

    async def _invalidate_dashboard_cache(self):
        """Clear dashboard cache when data changes"""
        await cache.delete(dashboard_cache_key())

    async def get_expense(self, expense_id: int, current_user: User = None) -> Optional[ExpenseNonContract]:
        """Get expense by ID with optional ownership check"""
        query = select(ExpenseNonContract).options(
            joinedload(ExpenseNonContract.upstream_contract)
        ).where(ExpenseNonContract.id == expense_id)
        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()
        
        # If current_user provided and not allowed to view all, check ownership
        if expense and current_user and not self._can_view_all_expenses(current_user):
            if expense.created_by != current_user.id:
                return None  # Return None to simulate "not found" for unauthorized access
        
        return expense

    async def list_expenses(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        expense_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        upstream_contract_id: Optional[int] = None,
        current_user: User = None
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

        # Data isolation: non-admin users can only see their own records
        if current_user and not self._can_view_all_expenses(current_user):
            query = query.where(ExpenseNonContract.created_by == current_user.id)

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
        upstream_contract_id: Optional[int] = None,
        current_user: User = None
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

        # Data isolation: non-admin users can only see their own records
        if current_user and not self._can_view_all_expenses(current_user):
            query = query.where(ExpenseNonContract.created_by == current_user.id)

        query = query.order_by(desc(ExpenseNonContract.created_at))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_expense(self, expense_in: ExpenseCreate, user: User) -> ExpenseNonContract:
        """Create new expense"""
        data = expense_in.model_dump()
        
        # Auto-generate expense code if not provided or empty (use expense_date for year/month)
        if not data.get('expense_code') or data['expense_code'].strip() == '':
            code_generator = ContractCodeGenerator(self.db)
            expense_date = data.get('expense_date')
            data['expense_code'] = await code_generator.generate_expense_code(expense_date)
        
        # Check for duplicate expense code
        existing = await self.db.execute(select(ExpenseNonContract).where(ExpenseNonContract.expense_code == data['expense_code']))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="费用编号已存在")
            
        expense = ExpenseNonContract(**data, created_by=user.id, updated_by=user.id)
        self.db.add(expense)
        await self.db.flush()
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
        await self.db.commit()
        await self.db.refresh(expense)
        
        await self._invalidate_dashboard_cache()
        
        # Return with relationship
        return await self.get_expense(expense.id)

    async def update_expense(self, expense_id: int, expense_in: ExpenseUpdate, user: User) -> ExpenseNonContract:
        """Update existing expense with ownership check"""
        # Use get_expense without user param first to get the raw expense
        query = select(ExpenseNonContract).options(
            joinedload(ExpenseNonContract.upstream_contract)
        ).where(ExpenseNonContract.id == expense_id)
        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
        
        # Ownership check: non-admin users can only edit their own records
        if not self._can_view_all_expenses(user):
            if expense.created_by != user.id:
                raise HTTPException(status_code=403, detail="权限不足：您只能编辑自己创建的费用记录")

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
        await self.db.commit()
        await self.db.refresh(expense)
        
        await self._invalidate_dashboard_cache()

        return expense

    async def delete_expense(self, expense_id: int, user: User) -> None:
        """Delete expense with ownership check"""
        # Use get_expense without user param first to get the raw expense
        query = select(ExpenseNonContract).options(
            joinedload(ExpenseNonContract.upstream_contract)
        ).where(ExpenseNonContract.id == expense_id)
        result = await self.db.execute(query)
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
        
        # Ownership check: non-admin users can only delete their own records
        if not self._can_view_all_expenses(user):
            if expense.created_by != user.id:
                raise HTTPException(status_code=403, detail="权限不足：您只能删除自己创建的费用记录")
        
        expense_code = expense.expense_code
        expense_data = {
            "id": expense.id,
            "expense_code": expense.expense_code,
            "description": expense.description
        }
            
        await self.db.delete(expense)
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
        await self.db.commit()
        
        await self._invalidate_dashboard_cache()

    async def approve_expense(self, expense_id: int, approved: bool, user: User) -> None:
        """Approve or reject expense"""
        expense = await self.get_expense(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
            
        expense.status = "已审核" if approved else "已驳回"
        expense.approved_by = user.id
        expense.approved_at = datetime.utcnow()

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
        
        await self.db.commit()
        await self._invalidate_dashboard_cache()
