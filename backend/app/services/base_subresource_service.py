"""
Generic Sub-Resource Service Base Class
Eliminates code duplication across contract sub-resources (receivables, invoices, receipts, settlements)
"""
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import DeclarativeMeta

from app.core.errors import ResourceNotFoundError, ValidationError

T = TypeVar('T')


class SubResourceService(Generic[T]):
    """Generic service for managing contract sub-resources"""

    def __init__(self, db: AsyncSession, model: Type[T], resource_name: str):
        self.db = db
        self.model = model
        self.resource_name = resource_name

    async def create(self, contract_id: int, data: Dict[str, Any], user_id: int) -> T:
        """Create a new sub-resource"""
        if data.get('contract_id') != contract_id:
            raise ValidationError(
                message="合同ID不匹配",
                field_errors={"contract_id": "路径参数与请求体中的合同ID不一致"}
            )

        obj = self.model(**data, created_by=user_id, updated_by=user_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_by_contract(self, contract_id: int) -> List[T]:
        """List all sub-resources for a contract"""
        query = select(self.model).where(self.model.contract_id == contract_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, contract_id: int, resource_id: int) -> Optional[T]:
        """Get a specific sub-resource"""
        query = select(self.model).where(
            self.model.id == resource_id,
            self.model.contract_id == contract_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        contract_id: int,
        resource_id: int,
        data: Dict[str, Any],
        user_id: int
    ) -> T:
        """Update a sub-resource"""
        obj = await self.get_by_id(contract_id, resource_id)
        if not obj:
            raise ResourceNotFoundError(
                resource_type=self.resource_name,
                resource_id=resource_id
            )

        update_data = {k: v for k, v in data.items() if k != 'contract_id'}
        for key, value in update_data.items():
            setattr(obj, key, value)

        obj.updated_by = user_id
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, contract_id: int, resource_id: int) -> None:
        """Delete a sub-resource"""
        obj = await self.get_by_id(contract_id, resource_id)
        if not obj:
            raise ResourceNotFoundError(
                resource_type=self.resource_name,
                resource_id=resource_id
            )

        await self.db.delete(obj)
        await self.db.commit()
