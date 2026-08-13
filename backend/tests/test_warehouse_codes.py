"""Material code generation and uniqueness."""

import asyncio
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.models.user import User
from app.models.warehouse import (
    MaterialCategory,
    MaterialCondition,
    SupplyType,
    WarehouseMaterial,
)
from app.services.warehouse.codes import generate_material_code, material_identity_key
from tests.conftest import TEST_DATABASE_URL as CONFT_TEST_DB


@pytest.mark.asyncio
async def test_material_code_format_and_segments(test_db: AsyncSession):
    code_j = await generate_material_code(
        test_db, MaterialCategory.ZC, SupplyType.J, MaterialCondition.NEW
    )
    code_jf = await generate_material_code(
        test_db, MaterialCategory.ZC, SupplyType.J, MaterialCondition.SCRAP
    )
    code_fc = await generate_material_code(
        test_db, MaterialCategory.FC, SupplyType.Y, MaterialCondition.NEW
    )
    await test_db.commit()

    assert code_j == "ZC-J-001"
    assert code_jf == "ZC-JF-001"
    assert code_fc == "FC-Y-001"


@pytest.mark.asyncio
async def test_archived_codes_are_not_reused(test_db: AsyncSession, test_admin: User):
    first = await generate_material_code(
        test_db, MaterialCategory.GJ, SupplyType.Y, MaterialCondition.NEW
    )
    material = WarehouseMaterial(
        code=first,
        category="GJ",
        supply_type="Y",
        condition="NEW",
        name="扳手",
        brand="A",
        specification="8寸",
        unit="把",
        identity_key=material_identity_key("扳手", "A", "8寸", "把", "NEW", "Y"),
        is_active=False,
        created_by=test_admin.id,
    )
    test_db.add(material)
    await test_db.commit()

    second = await generate_material_code(
        test_db, MaterialCategory.GJ, SupplyType.Y, MaterialCondition.NEW
    )
    await test_db.commit()
    assert first == "GJ-Y-001"
    assert second == "GJ-Y-002"


@pytest.mark.asyncio
async def test_concurrent_material_codes_are_unique(test_db: AsyncSession, test_admin: User):
    engine = create_async_engine(CONFT_TEST_DB, poolclass=NullPool)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def create_one(index: int) -> str:
        async with Session() as session:
            code = await generate_material_code(
                session, MaterialCategory.LB, SupplyType.J, MaterialCondition.NEW
            )
            session.add(
                WarehouseMaterial(
                    code=code,
                    category="LB",
                    supply_type="J",
                    condition="NEW",
                    name=f"手套-{index}",
                    brand="B",
                    specification="L",
                    unit="双",
                    minimum_stock=Decimal("0"),
                    identity_key=material_identity_key(
                        f"手套-{index}", "B", "L", "双", "NEW", "J"
                    ),
                    is_active=True,
                    created_by=test_admin.id,
                )
            )
            await session.commit()
            return code

    codes = await asyncio.gather(*[create_one(i) for i in range(20)])
    await engine.dispose()

    assert len(codes) == 20
    assert len(set(codes)) == 20
    assert "LB-J-001" in codes
    assert max(int(code.split("-")[-1]) for code in codes) == 20
    assert min(int(code.split("-")[-1]) for code in codes) == 1
