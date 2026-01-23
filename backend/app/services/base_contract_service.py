from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException
from app.services.cache import cache, dashboard_cache_key

ModelType = TypeVar("ModelType")

class BaseContractService(Generic[ModelType]):
    """
    Base service for contract operations to reduce code duplication.
    """
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def _invalidate_dashboard_cache(self):
        """Clear dashboard cache when contract data changes"""
        await cache.delete(dashboard_cache_key())

    async def get_contract(self, contract_id: int) -> Optional[ModelType]:
        """Get contract by ID (Basic retrieval, override for relations)"""
        result = await self.db.execute(select(self.model).where(self.model.id == contract_id))
        return result.scalar_one_or_none()
    
    async def get_next_serial_number(self) -> int:
        """Get the next available serial number"""
        query = select(func.max(self.model.serial_number))
        result = await self.db.execute(query)
        max_sn = result.scalar_one_or_none()
        return (max_sn or 0) + 1

    async def check_serial_number_exists(self, serial_number: int, exclude_id: Optional[int] = None) -> bool:
        """Check if serial number exists"""
        if not serial_number:
            return False
            
        query = select(self.model).where(self.model.serial_number == serial_number)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
            
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def check_contract_code_exists(self, contract_code: str, exclude_id: Optional[int] = None) -> Optional[ModelType]:
        """Check if contract code exists and return the conflicting contract"""
        if not contract_code:
            return None
            
        query = select(self.model).where(self.model.contract_code == contract_code)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
            
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
