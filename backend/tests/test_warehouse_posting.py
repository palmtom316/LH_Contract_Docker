"""Inventory posting engine: inbound, outbound, transfer, void, rebuild, concurrency."""

import asyncio
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.errors import AppException, ErrorCode
from app.models.user import User
from app.models.warehouse import WarehouseDocument, WarehouseLedgerEntry, WarehouseStockBalance
from app.services.warehouse.posting import WarehousePostingService, quantize_qty
from tests.conftest import TEST_DATABASE_URL
from tests.warehouse_fixtures import seed_two_warehouses


async def _qty(db: AsyncSession, warehouse_id: int, location_id: int, project_id: int, material_id: int):
    result = await db.execute(
        select(WarehouseStockBalance.quantity).where(
            WarehouseStockBalance.warehouse_id == warehouse_id,
            WarehouseStockBalance.location_id == location_id,
            WarehouseStockBalance.project_id == project_id,
            WarehouseStockBalance.material_id == material_id,
        )
    )
    value = result.scalar_one_or_none()
    return quantize_qty(value or 0)


@pytest.mark.asyncio
async def test_inbound_outbound_transfer_and_company_total(
    test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    service = WarehousePostingService(test_db, test_admin)

    await service.post_inbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="张三",
        business_type="PURCHASE",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("20")}],
        idempotency_key="in-20",
    )
    await service.post_outbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="张三",
        business_type="ISSUE",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("4")}],
        idempotency_key="out-4",
    )
    await service.post_transfer(
        occurred_on=date(2026, 8, 13),
        handler="张三",
        reference_no="调拨依据-001",
        lines=[
            {
                "material_id": ctx.material.id,
                "quantity": Decimal("6"),
                "source_warehouse_id": ctx.wh1.id,
                "source_location_id": ctx.loc1.id,
                "source_project_id": ctx.project_a.id,
                "target_warehouse_id": ctx.wh2.id,
                "target_location_id": ctx.loc2.id,
                "target_project_id": ctx.project_b.id,
            }
        ],
        idempotency_key="tr-6",
    )
    await test_db.commit()

    qty_a = await _qty(test_db, ctx.wh1.id, ctx.loc1.id, ctx.project_a.id, ctx.material.id)
    qty_b = await _qty(test_db, ctx.wh2.id, ctx.loc2.id, ctx.project_b.id, ctx.material.id)
    assert qty_a == Decimal("10.0000")
    assert qty_b == Decimal("6.0000")

    total = await test_db.execute(select(func.coalesce(func.sum(WarehouseStockBalance.quantity), 0)))
    assert quantize_qty(total.scalar_one()) == Decimal("16.0000")


@pytest.mark.asyncio
async def test_idempotent_inbound_does_not_double_post(
    test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    service = WarehousePostingService(test_db, test_admin)
    first = await service.post_inbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="李四",
        business_type="OPENING",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("5")}],
        idempotency_key="same-key",
    )
    second = await service.post_inbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="李四",
        business_type="OPENING",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("5")}],
        idempotency_key="same-key",
    )
    await test_db.commit()
    assert first.id == second.id
    qty = await _qty(test_db, ctx.wh1.id, ctx.loc1.id, ctx.project_a.id, ctx.material.id)
    assert qty == Decimal("5.0000")


@pytest.mark.asyncio
async def test_void_transfer_restores_balances(test_db: AsyncSession, test_admin: User):
    ctx = await seed_two_warehouses(test_db, test_admin)
    service = WarehousePostingService(test_db, test_admin)
    await service.post_inbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="王五",
        business_type="PURCHASE",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("10")}],
        idempotency_key="in-10",
    )
    transfer = await service.post_transfer(
        occurred_on=date(2026, 8, 13),
        handler="王五",
        reference_no="调拨依据-002",
        lines=[
            {
                "material_id": ctx.material.id,
                "quantity": Decimal("3"),
                "source_warehouse_id": ctx.wh1.id,
                "source_location_id": ctx.loc1.id,
                "source_project_id": ctx.project_a.id,
                "target_warehouse_id": ctx.wh2.id,
                "target_location_id": ctx.loc2.id,
                "target_project_id": ctx.project_b.id,
            }
        ],
        idempotency_key="tr-3",
    )
    reversal = await service.void_document(transfer.id, "录错项目", idempotency_key="void-tr-3")
    await test_db.commit()

    assert reversal.document_type == "REVERSAL"
    refreshed = await service.get_document(transfer.id)
    assert refreshed.status == "VOIDED"
    qty_a = await _qty(test_db, ctx.wh1.id, ctx.loc1.id, ctx.project_a.id, ctx.material.id)
    qty_b = await _qty(test_db, ctx.wh2.id, ctx.loc2.id, ctx.project_b.id, ctx.material.id)
    assert qty_a == Decimal("10.0000")
    assert qty_b == Decimal("0.0000")


@pytest.mark.asyncio
async def test_rebuild_balances_matches_ledger(test_db: AsyncSession, test_admin: User):
    ctx = await seed_two_warehouses(test_db, test_admin)
    service = WarehousePostingService(test_db, test_admin)
    await service.post_inbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="赵六",
        business_type="PURCHASE",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("8")}],
        idempotency_key="in-8",
    )
    await test_db.commit()
    balance = (
        await test_db.execute(select(WarehouseStockBalance))
    ).scalar_one()
    balance.quantity = Decimal("1")
    await test_db.commit()

    check = await service.rebuild_balances(repair=False)
    assert check["mismatches"] == 1
    repaired = await service.rebuild_balances(repair=True)
    await test_db.commit()
    assert repaired["repaired"] is True
    qty = await _qty(test_db, ctx.wh1.id, ctx.loc1.id, ctx.project_a.id, ctx.material.id)
    assert qty == Decimal("8.0000")


@pytest.mark.asyncio
async def test_concurrent_outbound_only_one_consumes_last_stock(
    test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    service = WarehousePostingService(test_db, test_admin)
    await service.post_inbound(
        warehouse_id=ctx.wh1.id,
        location_id=ctx.loc1.id,
        project_id=ctx.project_a.id,
        occurred_on=date(2026, 8, 13),
        handler="admin",
        business_type="OPENING",
        lines=[{"material_id": ctx.material.id, "quantity": Decimal("6")}],
        idempotency_key="open-6",
    )
    await test_db.commit()

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def try_outbound(key: str):
        async with Session() as session:
            posting = WarehousePostingService(session, test_admin)
            try:
                await posting.post_outbound(
                    warehouse_id=ctx.wh1.id,
                    location_id=ctx.loc1.id,
                    project_id=ctx.project_a.id,
                    occurred_on=date(2026, 8, 13),
                    handler="并发",
                    business_type="ISSUE",
                    lines=[{"material_id": ctx.material.id, "quantity": Decimal("4")}],
                    idempotency_key=key,
                )
                await session.commit()
                return "ok"
            except AppException as exc:
                await session.rollback()
                return exc.error_code.value

    first, second = await asyncio.gather(try_outbound("c1"), try_outbound("c2"))
    await engine.dispose()

    assert {first, second} == {"ok", ErrorCode.INSUFFICIENT_STOCK.value}
    qty = await _qty(test_db, ctx.wh1.id, ctx.loc1.id, ctx.project_a.id, ctx.material.id)
    assert qty == Decimal("2.0000")
    count = await test_db.execute(select(func.count(WarehouseDocument.id)))
    assert count.scalar_one() == 2  # inbound + one outbound
    ledger_count = await test_db.execute(select(func.count(WarehouseLedgerEntry.id)))
    assert ledger_count.scalar_one() == 2


@pytest.mark.asyncio
async def test_identical_transfer_dimension_rejected(test_db: AsyncSession, test_admin: User):
    ctx = await seed_two_warehouses(test_db, test_admin)
    service = WarehousePostingService(test_db, test_admin)
    with pytest.raises(Exception):
        await service.post_transfer(
            occurred_on=date(2026, 8, 13),
            handler="x",
            reference_no="same",
            lines=[
                {
                    "material_id": ctx.material.id,
                    "quantity": Decimal("1"),
                    "source_warehouse_id": ctx.wh1.id,
                    "source_location_id": ctx.loc1.id,
                    "source_project_id": ctx.project_a.id,
                    "target_warehouse_id": ctx.wh1.id,
                    "target_location_id": ctx.loc1.id,
                    "target_project_id": ctx.project_a.id,
                }
            ],
        )
