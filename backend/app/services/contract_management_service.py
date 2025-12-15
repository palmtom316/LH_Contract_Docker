from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.contract_management import (
    ContractManagement,
    FinanceManagementPayable,
    FinanceManagementPayment,
    ManagementSettlement
)
from app.models.contract_upstream import ContractUpstream
from app.schemas.contract_management import ContractManagementCreate, ContractManagementUpdate
from app.services.cache import cache, dashboard_cache_key
from app.services.status_service import calculate_contract_status
from app.models.user import User
from app.services.audit_service import create_audit_log, AuditAction, ResourceType

class ContractManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _invalidate_dashboard_cache(self):
        """Clear dashboard cache when contract data changes"""
        await cache.delete(dashboard_cache_key())

    async def get_contract(self, contract_id: int) -> Optional[ContractManagement]:
        """Get contract by ID (with upstream relation for common usage)"""
        query = select(ContractManagement).options(
            selectinload(ContractManagement.upstream_contract),
            selectinload(ContractManagement.payables),
            selectinload(ContractManagement.invoices),
            selectinload(ContractManagement.payments),
            selectinload(ContractManagement.settlements)
        ).where(ContractManagement.id == contract_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_contract_with_relations(self, contract_id: int) -> Optional[ContractManagement]:
        """Get contract by ID with all financial relations loaded"""
        return await self.get_contract(contract_id)

    async def list_contracts(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List contracts with filtering and pagination"""
        query = select(ContractManagement).options(
            selectinload(ContractManagement.upstream_contract),
            selectinload(ContractManagement.payables),
            selectinload(ContractManagement.invoices),
            selectinload(ContractManagement.payments),
            selectinload(ContractManagement.settlements)
        )

        if keyword:
            conditions = [
                ContractManagement.contract_name.ilike(f"%{keyword}%"),
                ContractManagement.contract_code.ilike(f"%{keyword}%"),
                ContractManagement.party_a_name.ilike(f"%{keyword}%"),
                ContractManagement.party_b_name.ilike(f"%{keyword}%")
            ]
            if keyword.isdigit():
                conditions.append(ContractManagement.serial_number == int(keyword))
                conditions.append(ContractManagement.id == int(keyword))
            
            query = query.where(or_(*conditions))

        if status:
            query = query.where(ContractManagement.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Pagination
        query = query.order_by(desc(ContractManagement.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        contracts = result.scalars().all()

        return {
            "items": contracts,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def list_all_contracts(self, keyword: Optional[str] = None, status: Optional[str] = None) -> List[ContractManagement]:
        """List all contracts for export (no pagination)"""
        query = select(ContractManagement).options(
            selectinload(ContractManagement.upstream_contract),
            selectinload(ContractManagement.payables),
            selectinload(ContractManagement.invoices),
            selectinload(ContractManagement.payments),
            selectinload(ContractManagement.settlements)
        )

        if keyword:
            conditions = [
                ContractManagement.contract_name.ilike(f"%{keyword}%"),
                ContractManagement.contract_code.ilike(f"%{keyword}%"),
                ContractManagement.party_a_name.ilike(f"%{keyword}%"),
                ContractManagement.party_b_name.ilike(f"%{keyword}%")
            ]
            if keyword.isdigit():
                conditions.append(ContractManagement.serial_number == int(keyword))
                conditions.append(ContractManagement.id == int(keyword))
            query = query.where(or_(*conditions))

        if status:
            query = query.where(ContractManagement.status == status)

        query = query.order_by(desc(ContractManagement.created_at))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_contract(self, contract_in: ContractManagementCreate, user: User) -> ContractManagement:
        """Create new management contract"""
        # Check unique serial_number
        if contract_in.serial_number:
            existing_sn = await self.db.execute(
                select(ContractManagement).where(ContractManagement.serial_number == contract_in.serial_number)
            )
            if existing_sn.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"合同序号 {contract_in.serial_number} 已存在")

        # Check unique contract_code
        existing = await self.db.execute(
            select(ContractManagement).where(ContractManagement.contract_code == contract_in.contract_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="合同编号已存在")

        contract = ContractManagement(**contract_in.model_dump(), created_by=user.id)
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._invalidate_dashboard_cache()

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.CREATE,
            resource_type=ResourceType.MANAGEMENT_CONTRACT,
            resource_id=contract.id,
            resource_name=contract.contract_name,
            new_values=contract_in.model_dump(mode='json'),
            description=f"创建管理合同: {contract.contract_name}"
        )
        
        # Return partial loaded object
        return await self.get_contract(contract.id)

    async def update_contract(self, contract_id: int, contract_in: ContractManagementUpdate, user: User) -> ContractManagement:
        """Update existing contract"""
        contract = await self.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")

        old_values = {
            k: getattr(contract, k) for k in contract_in.model_dump(exclude_unset=True).keys() 
            if hasattr(contract, k)
        }

        update_data = contract_in.model_dump(exclude_unset=True, exclude={'upstream_contract_name_snapshot'})

        # Check serial_number uniqueness
        if 'serial_number' in update_data and update_data['serial_number'] != contract.serial_number:
            if update_data['serial_number']:
                existing_sn = await self.db.execute(
                    select(ContractManagement).where(ContractManagement.serial_number == update_data['serial_number'])
                )
                if existing_sn.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail=f"合同序号 {update_data['serial_number']} 已存在")

        # Check contract_code uniqueness
        if 'contract_code' in update_data and update_data['contract_code'] != contract.contract_code:
            existing = await self.db.execute(
                select(ContractManagement).where(
                    ContractManagement.contract_code == update_data['contract_code'],
                    ContractManagement.id != contract_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="合同编号已存在")

        for field, value in update_data.items():
            setattr(contract, field, value)

        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._invalidate_dashboard_cache()

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.UPDATE,
            resource_type=ResourceType.MANAGEMENT_CONTRACT,
            resource_id=contract.id,
            resource_name=contract.contract_name,
            old_values=old_values,
            new_values=update_data,
            description=f"更新管理合同: {contract.contract_name}"
        )

        return contract

    async def delete_contract(self, contract_id: int, user: User) -> None:
        """Delete contract"""
        contract = await self.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
        
        contract_name = contract.contract_name
        contract_data = {
            "id": contract.id,
            "serial_number": contract.serial_number,
            "contract_name": contract.contract_name,
            "contract_code": contract.contract_code
        }

        await self.db.delete(contract)
        await self.db.commit()
        
        await self._invalidate_dashboard_cache()

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.DELETE,
            resource_type=ResourceType.MANAGEMENT_CONTRACT,
            resource_id=contract_id,
            resource_name=contract_name,
            old_values=contract_data,
            description=f"删除管理合同: {contract_name}"
        )

    async def refresh_contract_status(self, contract_id: int) -> None:
        """Recalculate and update contract status"""
        contract = await self.get_contract_with_relations(contract_id)
        if not contract:
            return

        # Calculate Totals
        total_settlement = sum(s.settlement_amount or 0 for s in contract.settlements)
        total_paid = sum(p.amount or 0 for p in contract.payments)
        total_payable = sum(p.amount or 0 for p in contract.payables)

        new_status = calculate_contract_status(contract, total_settlement, total_paid, total_payable)

        if contract.status != new_status:
            contract.status = new_status
            self.db.add(contract)
            await self.db.commit()
            
        await self._invalidate_dashboard_cache()
