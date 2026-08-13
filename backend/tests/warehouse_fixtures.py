"""Shared warehouse test fixtures."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.warehouse import (
    MaterialCategory,
    MaterialCondition,
    SupplyType,
    Warehouse,
    WarehouseLocation,
    WarehouseMaterial,
    WarehouseProject,
)
from app.services.warehouse.codes import generate_material_code, material_identity_key


@dataclass
class WarehouseSeed:
    wh1: Warehouse
    wh2: Warehouse
    loc1: WarehouseLocation
    loc2: WarehouseLocation
    project_a: WarehouseProject
    project_b: WarehouseProject
    material: WarehouseMaterial


async def seed_two_warehouses(db: AsyncSession, admin: User) -> WarehouseSeed:
    wh1 = Warehouse(code="WH1", name="一号库", is_active=True, created_by=admin.id)
    wh2 = Warehouse(code="WH2", name="二号库", is_active=True, created_by=admin.id)
    db.add_all([wh1, wh2])
    await db.flush()

    loc1 = WarehouseLocation(
        warehouse_id=wh1.id,
        code="STAGING",
        name="暂存区",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    loc2 = WarehouseLocation(
        warehouse_id=wh2.id,
        code="STAGING",
        name="暂存区",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    project_a = WarehouseProject(code="PA", name="A项目", is_active=True, created_by=admin.id)
    project_b = WarehouseProject(code="PB", name="B项目", is_active=True, created_by=admin.id)
    db.add_all([loc1, loc2, project_a, project_b])
    await db.flush()

    code = await generate_material_code(
        db, MaterialCategory.ZC, SupplyType.J, MaterialCondition.NEW
    )
    material = WarehouseMaterial(
        code=code,
        category=MaterialCategory.ZC.value,
        supply_type=SupplyType.J.value,
        condition=MaterialCondition.NEW.value,
        name="镀锌铁丝",
        brand="示例厂",
        specification="2.0mm",
        unit="圈",
        minimum_stock=Decimal("0"),
        identity_key=material_identity_key(
            "镀锌铁丝", "示例厂", "2.0mm", "圈", MaterialCondition.NEW, SupplyType.J
        ),
        is_active=True,
        created_by=admin.id,
    )
    db.add(material)
    await db.commit()
    await db.refresh(wh1)
    await db.refresh(wh2)
    await db.refresh(loc1)
    await db.refresh(loc2)
    await db.refresh(project_a)
    await db.refresh(project_b)
    await db.refresh(material)
    return WarehouseSeed(wh1, wh2, loc1, loc2, project_a, project_b, material)
