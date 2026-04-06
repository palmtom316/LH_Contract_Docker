from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, outerjoin
from sqlalchemy.orm import selectinload, aliased
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.contract_upstream import (
    ContractUpstream, 
    FinanceUpstreamReceivable, 
    FinanceUpstreamReceipt, 
    ProjectSettlement,
    FinanceUpstreamInvoice
)
from app.schemas.contract_upstream import ContractUpstreamCreate, ContractUpstreamUpdate
from app.services.cache import cache, dashboard_cache_key
from app.services.status_service import calculate_contract_status

from app.models.user import User
from app.services.audit_service import create_audit_log, AuditAction, ResourceType
from app.services.contract_code_generator import ContractCodeGenerator
from app.services.base_contract_service import BaseContractService


class ContractWrapper:
    """
    Wrapper to enforce SQL-calculated totals over model properties.
    Proxies all other attributes to the underlying contract model.
    """
    def __init__(self, contract, total_receivable, total_invoiced, total_received, total_settlement):
        self._contract = contract
        self._total_receivable = total_receivable or 0
        self._total_invoiced = total_invoiced or 0
        self._total_received = total_received or 0
        self._total_settlement = total_settlement or 0

    @property
    def total_receivable(self):
        return self._total_receivable

    @property
    def total_invoiced(self):
        return self._total_invoiced

    @property
    def total_received(self):
        return self._total_received

    @property
    def total_settlement(self):
        return self._total_settlement

    def __getattr__(self, name):
        return getattr(self._contract, name)


class ContractUpstreamService(BaseContractService[ContractUpstream]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ContractUpstream)

    async def get_contract(self, contract_id: int) -> Optional[ContractUpstream]:
        """Get contract by ID (Override to load relations)"""
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
        end_date: Optional[date] = None,
        company_category: Optional[str] = None,
        category: Optional[str] = None,
        management_mode: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """List contracts with filtering and pagination (Optimized with SQL aggregation)"""
        # 1. Prepare Subqueries for Totals
        # We use strict subqueries correlated to the main table
        
        # Receivables Sum
        receivables_sub = (
            select(func.sum(FinanceUpstreamReceivable.amount))
            .where(FinanceUpstreamReceivable.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )
        
        # Invoices Sum
        invoices_sub = (
            select(func.sum(FinanceUpstreamInvoice.amount))
            .where(FinanceUpstreamInvoice.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )
        
        # Receipts Sum
        receipts_sub = (
            select(func.sum(FinanceUpstreamReceipt.amount))
            .where(FinanceUpstreamReceipt.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )
        
        # Settlements Sum
        settlements_sub = (
            select(func.sum(ProjectSettlement.settlement_amount))
            .where(ProjectSettlement.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )

        # 2. Build Main Query
        # We select the Contract model AND the calculated scalar totals
        query = select(
            ContractUpstream,
            receivables_sub.label("total_receivable"),
            invoices_sub.label("total_invoiced"),
            receipts_sub.label("total_received"),
            settlements_sub.label("total_settlement")
        ).options(
            # We ONLY lazy/eager load what's strictly necessary for the "Card/List View" basic info if any.
            # Actually, we don't need any relationships for the list view now that totals are calculated.
            # But we might need 'settlements' for file paths in the PC view (audit_report_path etc from properties).
            # The properties `audit_report_path` etc rely on `latest_settlement`. 
            # If we don't load settlements, that property access triggers a query.
            # For performance, let's selectinload settlements (it's usually 0 or 1 record) but NOT the others.
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
                conditions.append(ContractUpstream.serial_number == int(keyword))
            
            query = query.where(or_(*conditions))
        
        if status:
            query = query.where(ContractUpstream.status == status)
            
        if company_category:
            query = query.where(ContractUpstream.company_category == company_category)
            
        if category:
            query = query.where(ContractUpstream.category == category)
            
        if management_mode:
            query = query.where(ContractUpstream.management_mode == management_mode)
            
        if start_date:
            query = query.where(ContractUpstream.sign_date >= start_date)
        if end_date:
            query = query.where(ContractUpstream.sign_date <= end_date)
            
        if start_month:
            try:
                s_year, s_month = map(int, start_month.split('-'))
                s_date = date(s_year, s_month, 1)
                query = query.where(ContractUpstream.sign_date >= s_date)
            except ValueError:
                pass 

        if end_month:
            try:
                e_year, e_month = map(int, end_month.split('-'))
                if e_month == 12:
                    e_date = date(e_year + 1, 1, 1)
                else:
                    e_date = date(e_year, e_month + 1, 1)
                query = query.where(ContractUpstream.sign_date < e_date)
            except ValueError:
                pass
            
        # Count total
        # We can use the same query structure but simple count
        # Note: count on the complex query is fine, or we can strip options
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        
        # Pagination
        query = query.order_by(desc(ContractUpstream.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        rows = result.all() # returns list of (ContractUpstream, t_rec, t_inv, t_receipt, t_settle)
        
        # 3. Wrap results
        items = [
            ContractWrapper(r[0], r[1], r[2], r[3], r[4]) 
            for r in rows
        ]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def list_all_contracts(
        self, 
        keyword: Optional[str] = None, 
        status: Optional[str] = None,
        company_category: Optional[str] = None,
        category: Optional[str] = None,
        management_mode: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> List[ContractUpstream]:
        """List all contracts for export (no pagination) - Optimized"""
        
        # Receivables Sum
        receivables_sub = (
            select(func.sum(FinanceUpstreamReceivable.amount))
            .where(FinanceUpstreamReceivable.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )
        
        # Invoices Sum
        invoices_sub = (
            select(func.sum(FinanceUpstreamInvoice.amount))
            .where(FinanceUpstreamInvoice.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )
        
        # Receipts Sum
        receipts_sub = (
            select(func.sum(FinanceUpstreamReceipt.amount))
            .where(FinanceUpstreamReceipt.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )
        
        # Settlements Sum
        settlements_sub = (
            select(func.sum(ProjectSettlement.settlement_amount))
            .where(ProjectSettlement.contract_id == ContractUpstream.id)
            .correlate(ContractUpstream)
            .scalar_subquery()
        )

        query = select(
            ContractUpstream,
            receivables_sub.label("total_receivable"),
            invoices_sub.label("total_invoiced"),
            receipts_sub.label("total_received"),
            settlements_sub.label("total_settlement")
        ).options(
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
                conditions.append(ContractUpstream.serial_number == int(keyword))
            query = query.where(or_(*conditions))
        
        if status:
            query = query.where(ContractUpstream.status == status)
            
        if company_category:
            query = query.where(ContractUpstream.company_category == company_category)
            
        if category:
            query = query.where(ContractUpstream.category == category)
            
        if management_mode:
            query = query.where(ContractUpstream.management_mode == management_mode)
            
        if start_date:
            query = query.where(ContractUpstream.sign_date >= start_date)
        if end_date:
            query = query.where(ContractUpstream.sign_date <= end_date)
            
        if start_month:
            try:
                s_year, s_month = map(int, start_month.split('-'))
                s_date = date(s_year, s_month, 1)
                query = query.where(ContractUpstream.sign_date >= s_date)
            except ValueError:
                pass

        if end_month:
            try:
                e_year, e_month = map(int, end_month.split('-'))
                if e_month == 12:
                    e_date = date(e_year + 1, 1, 1)
                else:
                    e_date = date(e_year, e_month + 1, 1)
                query = query.where(ContractUpstream.sign_date < e_date)
            except ValueError:
                pass
            
        query = query.order_by(desc(ContractUpstream.created_at))
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            ContractWrapper(r[0], r[1], r[2], r[3], r[4]) 
            for r in rows
        ]

    async def create_contract(self, contract_in: ContractUpstreamCreate, user: User) -> ContractUpstream:
        """Create a new contract"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Get data from input (category, pricing_mode, management_mode are now stored as strings)
        data = contract_in.model_dump()
        
        # Auto-generate contract code if not provided or empty (use sign_date for year/month)
        if not data.get('contract_code') or data['contract_code'].strip() == '':
            code_generator = ContractCodeGenerator(self.db)
            # 使用签约日期生成编号
            sign_date = data.get('sign_date')
            data['contract_code'] = await code_generator.generate_upstream_code(sign_date)
            logger.info(f"Auto-generated contract code: {data['contract_code']} (based on sign_date: {sign_date})")

        try:
            logger.info(f"Creating contract with code: {data['contract_code']}")
            
            # Check unique serial_number
            if contract_in.serial_number:
                logger.info(f"Checking serial_number: {contract_in.serial_number}")
                if await self.check_serial_number_exists(contract_in.serial_number):
                    raise HTTPException(status_code=400, detail=f"合同序号 {contract_in.serial_number} 已存在")
            
            # Check unique contract_code
            logger.info(f"Checking contract_code: {data['contract_code']}")
            existing_contract = await self.check_contract_code_exists(data['contract_code'])
            if existing_contract:
                raise HTTPException(
                    status_code=400, 
                    detail=f"合同编号 '{data['contract_code']}' 已被使用（合同名称：{existing_contract.contract_name}），请使用其他编号"
                )
            
            logger.info("Creating contract object...")
            contract = ContractUpstream(**data, created_by=user.id)
            
            logger.info("Adding to database...")
            self.db.add(contract)

            # Audit Log
            await self.db.flush()
            await create_audit_log(
                db=self.db,
                user=user,
                action=AuditAction.CREATE,
                resource_type=ResourceType.UPSTREAM_CONTRACT,
                resource_id=contract.id,
                resource_name=contract.contract_name,
                new_values=contract_in.model_dump(mode='json'),
                description=f"创建上游合同: {contract.contract_name}"
            )
            
            logger.info("Committing...")
            await self.db.commit()
            
            logger.info("Refreshing...")
            await self.db.refresh(contract)
            
            logger.info("Invalidating cache...")
            await self._invalidate_dashboard_cache()
            
            logger.info(f"Contract created successfully: ID={contract.id}")
            return contract
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating contract: {e}", exc_info=True)
            raise

    async def update_contract(self, contract_id: int, contract_in: ContractUpstreamUpdate, user: User) -> ContractUpstream:
        """Update existing contract"""
        contract = await self.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
            
        old_values = {
            k: getattr(contract, k) for k in contract_in.model_dump(exclude_unset=True).keys() 
            if hasattr(contract, k)
        }

        update_data = contract_in.model_dump(exclude_unset=True)
        
        # Check serial_number uniqueness
        if 'serial_number' in update_data and update_data['serial_number'] != contract.serial_number:
            if await self.check_serial_number_exists(update_data['serial_number'], exclude_id=contract_id):
                 raise HTTPException(status_code=400, detail=f"合同序号 {update_data['serial_number']} 已存在")
        
        # Check contract_code uniqueness
        if 'contract_code' in update_data and update_data['contract_code'] != contract.contract_code:
            existing_contract = await self.check_contract_code_exists(update_data['contract_code'], exclude_id=contract_id)
            if existing_contract:
                raise HTTPException(
                    status_code=400, 
                    detail=f"合同编号 '{update_data['contract_code']}' 已被使用（合同名称：{existing_contract.contract_name}），请使用其他编号"
                )
        
        for field, value in update_data.items():
            setattr(contract, field, value)

        # Audit Log
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.UPDATE,
            resource_type=ResourceType.UPSTREAM_CONTRACT,
            resource_id=contract.id,
            resource_name=contract.contract_name,
            old_values=old_values,
            new_values=update_data,
            description=f"更新上游合同: {contract.contract_name}"
        )
        
        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._invalidate_dashboard_cache()

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
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.DELETE,
            resource_type=ResourceType.UPSTREAM_CONTRACT,
            resource_id=contract_id,
            resource_name=contract_name,
            old_values=contract_data,
            description=f"删除上游合同: {contract_name}"
        )
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
                # (category, pricing_mode, management_mode are stored as strings from dictionary)

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
