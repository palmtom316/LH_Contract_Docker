from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.contract_upstream import (
    ContractUpstream, 
    FinanceUpstreamReceivable, 
    FinanceUpstreamReceipt, 
    ProjectSettlement
)
from app.schemas.contract_upstream import ContractUpstreamCreate, ContractUpstreamUpdate
from app.services.cache import cache, dashboard_cache_key
from app.services.status_service import calculate_contract_status

class ContractUpstreamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _invalidate_dashboard_cache(self):
        """Clear dashboard cache when contract data changes"""
        await cache.delete(dashboard_cache_key())

    async def get_contract(self, contract_id: int) -> Optional[ContractUpstream]:
        """Get contract by ID"""
        query = select(ContractUpstream).options(
            selectinload(ContractUpstream.settlements),
            selectinload(ContractUpstream.receipts),
            selectinload(ContractUpstream.receivables),
            selectinload(ContractUpstream.invoices),
        ).where(ContractUpstream.id == contract_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_contract_with_relations(self, contract_id: int) -> Optional[ContractUpstream]:
        """Get contract by ID with all financial relations loaded"""
        return await self.get_contract(contract_id)

    async def list_contracts(
        self, 
        page: int = 1, 
        page_size: int = 10, 
        keyword: Optional[str] = None, 
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """List contracts with filtering and pagination"""
        query = select(ContractUpstream).options(
            selectinload(ContractUpstream.receivables),
            selectinload(ContractUpstream.invoices),
            selectinload(ContractUpstream.receipts),
            selectinload(ContractUpstream.settlements)
        )
        
        if keyword:
            conditions = [
                ContractUpstream.contract_name.ilike(f"%{keyword}%"),
                ContractUpstream.contract_code.ilike(f"%{keyword}%"),
                ContractUpstream.party_a_name.ilike(f"%{keyword}%"),
                ContractUpstream.party_b_name.ilike(f"%{keyword}%")
            ]
            if keyword.isdigit():
                conditions.append(ContractUpstream.id == int(keyword))
                conditions.append(ContractUpstream.serial_number == int(keyword))
            
            query = query.where(or_(*conditions))
        
        if status:
            query = query.where(ContractUpstream.status == status)
            
        if start_date:
            query = query.where(ContractUpstream.sign_date >= start_date)
        if end_date:
            query = query.where(ContractUpstream.sign_date <= end_date)
            
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        
        # Pagination
        query = query.order_by(desc(ContractUpstream.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        contracts = result.scalars().all()
        
        return {
            "items": contracts,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def list_all_contracts(self, keyword: Optional[str] = None, status: Optional[str] = None) -> List[ContractUpstream]:
        """List all contracts for export (no pagination)"""
        query = select(ContractUpstream).options(
            selectinload(ContractUpstream.receivables),
            selectinload(ContractUpstream.invoices),
            selectinload(ContractUpstream.receipts),
            selectinload(ContractUpstream.settlements)
        )
        
        if keyword:
            conditions = [
                ContractUpstream.contract_name.ilike(f"%{keyword}%"),
                ContractUpstream.contract_code.ilike(f"%{keyword}%"),
                ContractUpstream.party_a_name.ilike(f"%{keyword}%"),
                ContractUpstream.party_b_name.ilike(f"%{keyword}%")
            ]
            if keyword.isdigit():
                conditions.append(ContractUpstream.id == int(keyword))
                conditions.append(ContractUpstream.serial_number == int(keyword))
            query = query.where(or_(*conditions))
        
        if status:
            query = query.where(ContractUpstream.status == status)
            
        query = query.order_by(desc(ContractUpstream.created_at))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_contract(self, contract_in: ContractUpstreamCreate, user_id: int) -> ContractUpstream:
        """Create a new contract"""
        # Check unique serial_number
        if contract_in.serial_number:
            existing_sn = await self.db.execute(
                select(ContractUpstream).where(ContractUpstream.serial_number == contract_in.serial_number)
            )
            if existing_sn.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"合同序号 {contract_in.serial_number} 已存在")
        
        # Check unique contract_code
        existing = await self.db.execute(
            select(ContractUpstream).where(ContractUpstream.contract_code == contract_in.contract_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="合同编号已存在")
            
        contract = ContractUpstream(**contract_in.model_dump(), created_by=user_id)
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._invalidate_dashboard_cache()
        return contract

    async def update_contract(self, contract_id: int, contract_in: ContractUpstreamUpdate) -> ContractUpstream:
        """Update existing contract"""
        contract = await self.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
            
        update_data = contract_in.model_dump(exclude_unset=True)
        
        # Check serial_number uniqueness
        if 'serial_number' in update_data and update_data['serial_number'] != contract.serial_number:
            if update_data['serial_number']:
                existing_sn = await self.db.execute(
                    select(ContractUpstream).where(ContractUpstream.serial_number == update_data['serial_number'])
                )
                if existing_sn.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail=f"合同序号 {update_data['serial_number']} 已存在")
        
        # Check contract_code uniqueness
        if 'contract_code' in update_data and update_data['contract_code'] != contract.contract_code:
            existing = await self.db.execute(
                select(ContractUpstream).where(
                    ContractUpstream.contract_code == update_data['contract_code'],
                    ContractUpstream.id != contract_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="合同编号已存在")
        
        for field, value in update_data.items():
            setattr(contract, field, value)
            
        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._invalidate_dashboard_cache()
        return contract

    async def delete_contract(self, contract_id: int) -> None:
        """Delete contract"""
        contract = await self.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
            
        await self.db.delete(contract)
        await self.db.commit()
        
        await self._invalidate_dashboard_cache()

    async def refresh_contract_status(self, contract_id: int) -> None:
        """Recalculate and update contract status"""
        contract = await self.get_contract_with_relations(contract_id)
        if not contract:
            return

        # Calculate Totals
        total_settlement = sum(s.settlement_amount or 0 for s in contract.settlements)
        total_received = sum(r.amount or 0 for r in contract.receipts)
        total_receivable = sum(r.amount or 0 for r in contract.receivables)
        
        new_status = calculate_contract_status(contract, total_settlement, total_received, total_receivable)
        
        if contract.status != new_status:
            contract.status = new_status
            self.db.add(contract)
            # We don't necessarily update 'updated_at' for status auto-updates unless desired
            await self.db.commit()
        
        await self._invalidate_dashboard_cache()

    async def bulk_create_from_import(self, contracts_data: List[Dict], user_id: int) -> Dict[str, Any]:
        """
        Process validated data from import to create contracts.
        Returns: {success: int, errors: List[str]}
        """
        success_count = 0
        errors = []
        
        for idx, row in enumerate(contracts_data):
            try:
                # Double check existence just in case, though import logic usually checks batch beforehand.
                # However, individually checking here is safer for race conditions or mixed validation logic.
                
                # Check Code
                existing = await self.db.execute(
                    select(ContractUpstream).where(ContractUpstream.contract_code == row['contract_code'])
                )
                if existing.scalar_one_or_none():
                    errors.append(f"行 {idx+1}: 合同编号 '{row['contract_code']}' 已存在")
                    continue
                
                # Create Contract
                # Filter out None values to let defaults take over or allow nulls
                # Assuming row dict keys match ContractUpstream model fields
                
                contract = ContractUpstream(
                    **row,
                    created_by=user_id
                )
                self.db.add(contract)
                success_count += 1
                
            except Exception as e:
                errors.append(f"行 {idx+1}: {str(e)}")
        
        if success_count > 0:
            await self.db.commit()
            await self._invalidate_dashboard_cache()
            
        return {"success": success_count, "errors": errors}

    async def get_next_serial_number(self) -> int:
        """Get the next available serial number"""
        query = select(func.max(ContractUpstream.serial_number))
        result = await self.db.execute(query)
        max_sn = result.scalar_one_or_none()
        return (max_sn or 0) + 1
