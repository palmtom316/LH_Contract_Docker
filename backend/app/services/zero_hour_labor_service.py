from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import joinedload, selectinload
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.zero_hour_labor import ZeroHourLabor, ZeroHourLaborMaterial
from app.models.user import User
from app.schemas.zero_hour_labor import ZeroHourLaborCreate, ZeroHourLaborUpdate
from app.services.audit_service import create_audit_log, AuditAction, ResourceType

class ZeroHourLaborService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: int) -> Optional[ZeroHourLabor]:
        query = select(ZeroHourLabor).options(
            joinedload(ZeroHourLabor.upstream_contract),
            selectinload(ZeroHourLabor.materials)
        ).where(ZeroHourLabor.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        attribution: Optional[str] = None,
        upstream_contract_id: Optional[int] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        query = select(ZeroHourLabor).options(
            joinedload(ZeroHourLabor.upstream_contract),
            selectinload(ZeroHourLabor.materials)
        )

        if start_date:
            query = query.where(ZeroHourLabor.labor_date >= start_date)
        if end_date:
            query = query.where(ZeroHourLabor.labor_date <= end_date)
        if attribution:
            query = query.where(ZeroHourLabor.attribution == attribution)
        if upstream_contract_id:
            query = query.where(ZeroHourLabor.upstream_contract_id == upstream_contract_id)
        
        if keyword:
            conditions = [
                ZeroHourLabor.dispatch_unit.ilike(f"%{keyword}%")
                # Removed material_name search on main table, could add join search if needed
            ]
            query = query.where(or_(*conditions))

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Paging
        query = query.order_by(desc(ZeroHourLabor.labor_date), desc(ZeroHourLabor.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        # Unique is needed when using joinedload/selectinload sometimes, 
        # but with asyncpg/sqlalchemy recent versions it handles it well usually. 
        # Adding .unique() is safer for one-to-many joinedload.
        # But we used selectinload for materials, joinedload for contract.
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create(self, data_in: ZeroHourLaborCreate, user: User) -> ZeroHourLabor:
        import logging
        logger = logging.getLogger("app")
        try:
            data_dict = data_in.model_dump()
            materials_data = data_dict.pop("materials", [])
            
            logger.info(f"Creating ZeroHourLabor with data: {data_dict}")
            
            obj = ZeroHourLabor(**data_dict, created_by=user.id)
            self.db.add(obj)
            await self.db.flush()  # Flush to get ID
            
            # Add materials
            for mat in materials_data:
                material = ZeroHourLaborMaterial(**mat, zero_hour_labor_id=obj.id)
                self.db.add(material)
                
            await self.db.commit()
            await self.db.refresh(obj)
            
            # Reload to get relationships
            return await self.get(obj.id)
        except Exception as e:
            logger.error(f"Error creating ZeroHourLabor: {e}")
            raise

    async def update(self, id: int, data_in: ZeroHourLaborUpdate, user: User) -> ZeroHourLabor:
        obj = await self.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="记录不存在")
            
        old_values = {
            k: getattr(obj, k) for k in data_in.model_dump(exclude_unset=True).keys() 
            if hasattr(obj, k) and k != 'materials'
        }
        
        update_data = data_in.model_dump(exclude_unset=True)
        materials_data = update_data.pop("materials", None)
        
        for field, value in update_data.items():
            setattr(obj, field, value)
        
        # Handle materials update
        if materials_data is not None:
            # Delete existing
            # Note: cascade="all, delete-orphan" on relationship helps, but we need to clear the list
            # Or manually delete.
            # Easiest with SQLAlchemy ORM relationship:
            obj.materials.clear() # This creates DELETE statements if cascade is set
            # Add new
            for mat in materials_data:
                material = ZeroHourLaborMaterial(**mat) # ID will be auto-generated
                # We can append to relationship
                obj.materials.append(material)
                
        obj.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(obj)
        
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.UPDATE,
            resource_type=ResourceType.ZERO_HOUR_LABOR,
            resource_id=obj.id,
            resource_name=f"Labor-{obj.labor_date}",
            old_values=old_values,
            new_values=update_data,
            description="更新零星用工"
        )
        return await self.get(obj.id)

    async def delete(self, id: int, user: User) -> None:
        obj = await self.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        resource_name = f"Labor-{obj.labor_date}"
        
        await self.db.delete(obj)
        await self.db.commit()
        
        await create_audit_log(
            db=self.db,
            user=user,
            action=AuditAction.DELETE,
            resource_type=ResourceType.ZERO_HOUR_LABOR,
            resource_id=id,
            resource_name=resource_name,
            description="删除零星用工"
        )
