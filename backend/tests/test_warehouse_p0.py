"""P0 warehouse controls: counts, periods, supplements, rebuild, scrap, timezone."""

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.core.permissions import Permission, ROLE_PERMISSIONS
from app.core.timezone import BUSINESS_TZ_NAME, business_today
from app.models.user import User, UserRole
from app.models.warehouse import WarehouseUserScope
from app.services.auth import create_access_token, get_password_hash
from tests.warehouse_fixtures import seed_two_warehouses


def _headers(user: User, key: str | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'username': user.username, 'role': user.role.value})}"
    }
    if key:
        headers["Idempotency-Key"] = key
    return headers


async def _create_user(db: AsyncSession, username: str, role: UserRole) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name=username,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def test_business_today_uses_shanghai_calendar():
    utc_late = datetime(2026, 8, 18, 16, 30, tzinfo=ZoneInfo("UTC"))
    shanghai = utc_late.astimezone(ZoneInfo(BUSINESS_TZ_NAME)).date()
    assert shanghai == date(2026, 8, 19)
    assert business_today() == datetime.now(ZoneInfo(BUSINESS_TZ_NAME)).date()


def test_quantity_precision_respects_material_scale():
    from app.services.warehouse.posting import quantize_qty

    assert quantize_qty("1.23456", 3) == Decimal("1.235")
    assert quantize_qty("1.23456", 4) == Decimal("1.2346")


def test_warehouse_admin_has_p0_permissions():
    perms = ROLE_PERMISSIONS[UserRole.WAREHOUSE_ADMIN]
    assert Permission.MANAGE_WAREHOUSE_PERIODS in perms
    assert Permission.REPAIR_WAREHOUSE_BALANCES in perms
    assert Permission.SETTLE_WAREHOUSE_SCRAP in perms
    keeper = ROLE_PERMISSIONS[UserRole.COMPANY_STOREKEEPER]
    assert Permission.REPAIR_WAREHOUSE_BALANCES not in keeper
    assert Permission.MANAGE_WAREHOUSE_PERIODS not in keeper


@pytest.mark.asyncio
async def test_active_count_blocks_posting_until_voided(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "p0-in-1"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "OPENING",
            "lines": [{"material_id": ctx.material.id, "quantity": "10"}],
        },
    )
    assert inbound.status_code == 201

    created = await client.post(
        "/api/v1/warehouse/counts",
        headers=_headers(test_admin),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "counted_on": "2026-08-13",
        },
    )
    assert created.status_code == 201
    count = created.json()
    assert count["snapshot_source"] == "stock_balances"
    assert count["snapshot_at"]
    assert float(count["lines"][0]["book_quantity"]) == 10

    blocked = await client.post(
        "/api/v1/warehouse/outbounds",
        headers=_headers(test_admin, "p0-out-blocked"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "ISSUE",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert blocked.status_code == 409
    assert blocked.json()["error_code"] == ErrorCode.WAREHOUSE_CONFLICT.value

    voided = await client.post(
        f"/api/v1/warehouse/counts/{count['id']}/void",
        headers=_headers(test_admin),
        json={"reason": "盘点作废后继续作业"},
    )
    assert voided.status_code == 200
    assert voided.json()["status"] == "VOIDED"

    posted = await client.post(
        "/api/v1/warehouse/outbounds",
        headers=_headers(test_admin, "p0-out-ok"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "ISSUE",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert posted.status_code == 201


@pytest.mark.asyncio
async def test_closed_period_blocks_storekeeper_and_reopen_is_audited(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    keeper = await _create_user(test_db, "p0-keeper", UserRole.COMPANY_STOREKEEPER)
    test_db.add(
        WarehouseUserScope(user_id=keeper.id, warehouse_id=ctx.wh1.id, is_default=True)
    )
    await test_db.commit()

    seed = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "p0-period-seed"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "OPENING",
            "lines": [{"material_id": ctx.material.id, "quantity": "5"}],
        },
    )
    assert seed.status_code == 201

    closed = await client.post(
        "/api/v1/warehouse/periods/close",
        headers=_headers(test_admin),
        json={"year": 2026, "month": 8},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"

    denied = await client.post(
        "/api/v1/warehouse/outbounds",
        headers=_headers(keeper, "p0-period-keeper"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "keeper",
            "business_type": "ISSUE",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert denied.status_code == 409
    assert denied.json()["error_code"] == ErrorCode.PERIOD_CLOSED.value

    missing_reason = await client.post(
        "/api/v1/warehouse/periods/reopen",
        headers=_headers(test_admin),
        json={"year": 2026, "month": 8},
    )
    assert missing_reason.status_code == 422

    reopened = await client.post(
        "/api/v1/warehouse/periods/reopen",
        headers=_headers(test_admin),
        json={"year": 2026, "month": 8, "reason": "补录验收单"},
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "OPEN"
    assert reopened.json()["reopen_reason"] == "补录验收单"


@pytest.mark.asyncio
async def test_historical_period_requires_explicit_opening(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    denied = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "historical-period-denied"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2025-01-10",
            "handler": "admin",
            "business_type": "PURCHASE",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert denied.status_code == 409
    opened = await client.post(
        "/api/v1/warehouse/periods/open",
        headers=_headers(test_admin),
        json={"year": 2025, "month": 1, "reason": "历史验收单补录审批"},
    )
    assert opened.status_code == 200
    assert opened.json()["open_reason"] == "历史验收单补录审批"


@pytest.mark.asyncio
async def test_supplement_upsert_is_idempotent_and_keeps_history(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "p0-sup-in"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "PURCHASE",
            "supplier_name": "示例供应商",
            "purchase_order_no": "PO-1",
            "delivery_note_no": "DN-1",
            "acceptance_no": "AC-1",
            "acceptor": "验收员",
            "lines": [{"material_id": ctx.material.id, "quantity": "3"}],
        },
    )
    assert inbound.status_code == 201
    document_id = inbound.json()["id"]
    assert inbound.json()["supplier_name"] == "示例供应商"
    line_id = inbound.json()["lines"][0]["id"]

    first = await client.put(
        f"/api/v1/warehouse/documents/{document_id}/supplement",
        headers=_headers(test_admin),
        json={"document_line_id": line_id, "unit_price": "10", "amount": "30"},
    )
    assert first.status_code == 200
    assert first.json()["version"] == 1
    supplement_id = first.json()["id"]

    second = await client.put(
        f"/api/v1/warehouse/documents/{document_id}/supplement",
        headers=_headers(test_admin),
        json={"document_line_id": line_id, "unit_price": "12", "amount": "36"},
    )
    assert second.status_code == 200
    assert second.json()["id"] == supplement_id
    assert second.json()["version"] == 2
    assert Decimal(second.json()["unit_price"]) == Decimal("12.0000")

    listed = await client.get(
        f"/api/v1/warehouse/documents/{document_id}/supplement",
        headers=_headers(test_admin),
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    negative = await client.put(
        f"/api/v1/warehouse/documents/{document_id}/supplement",
        headers=_headers(test_admin),
        json={"document_line_id": line_id, "unit_price": "-1"},
    )
    assert negative.status_code == 422


@pytest.mark.asyncio
async def test_rebuild_repair_requires_reason_and_high_permission(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "p0-rebuild-in"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "OPENING",
            "lines": [{"material_id": ctx.material.id, "quantity": "8"}],
        },
    )
    assert inbound.status_code == 201

    preview = await client.post(
        "/api/v1/warehouse/stock-balances/rebuild",
        headers=_headers(test_admin),
        json={"repair": False},
    )
    assert preview.status_code == 200
    assert preview.json()["dry_run"] is True
    assert preview.json()["repaired"] is False

    missing = await client.post(
        "/api/v1/warehouse/stock-balances/rebuild",
        headers=_headers(test_admin),
        json={"repair": True},
    )
    assert missing.status_code == 422

    keeper = await _create_user(test_db, "p0-repair-keeper", UserRole.COMPANY_STOREKEEPER)
    test_db.add(
        WarehouseUserScope(user_id=keeper.id, warehouse_id=ctx.wh1.id, is_default=True)
    )
    await test_db.commit()
    denied = await client.post(
        "/api/v1/warehouse/stock-balances/rebuild",
        headers=_headers(keeper),
        json={"repair": True, "reason": "库管尝试修账"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_scrap_settle_requires_weight_and_recycler(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "p0-scrap-in"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "PURCHASE",
            "lines": [{"material_id": ctx.material.id, "quantity": "4"}],
        },
    )
    assert inbound.status_code == 201
    posted = await client.post(
        "/api/v1/warehouse/outbounds",
        headers=_headers(test_admin, "p0-scrap-out"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "SCRAP_DISPOSAL",
            "scrap_basis_file": "warehouse/2026/08/scrap.pdf",
            "scrap_basis_file_name": "废旧处理审批.pdf",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert posted.status_code == 201
    assert posted.json()["scrap_status"] == "PENDING"
    document_id = posted.json()["id"]

    incomplete = await client.post(
        f"/api/v1/warehouse/documents/{document_id}/scrap-settle",
        headers=_headers(test_admin),
        json={"scrap_status": "SETTLED"},
    )
    assert incomplete.status_code == 422

    settled = await client.post(
        f"/api/v1/warehouse/documents/{document_id}/scrap-settle",
        headers=_headers(test_admin),
        json={
            "scrap_weight": "1.2",
            "scrap_assessed_value": "80",
            "scrap_disposal_method": "回收",
            "scrap_recycler": "废旧回收站",
            "scrap_residual_value": "80",
            "scrap_status": "SETTLED",
        },
    )
    assert settled.status_code == 200
    assert settled.json()["scrap_status"] == "SETTLED"
    assert settled.json()["scrap_recycler"] == "废旧回收站"


@pytest.mark.asyncio
async def test_cannot_clear_default_location_on_active_warehouse(
    client: AsyncClient, test_admin: User
):
    created = await client.post(
        "/api/v1/warehouse/warehouses",
        headers=_headers(test_admin),
        json={"code": "WH-DEF", "name": "默认货位库"},
    )
    assert created.status_code == 201
    location_id = created.json()["locations"][0]["id"]
    blocked = await client.put(
        f"/api/v1/warehouse/locations/{location_id}",
        headers=_headers(test_admin),
        json={"is_default": False},
    )
    assert blocked.status_code == 422


@pytest.mark.asyncio
async def test_turnover_report_uses_net_balance(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    for key, path, quantity in (
        ("turnover-in", "inbounds", "10"),
        ("turnover-out", "outbounds", "3"),
    ):
        payload = {
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": business_today().isoformat(),
            "handler": "admin",
            "business_type": "PURCHASE" if path == "inbounds" else "ISSUE",
            "lines": [{"material_id": ctx.material.id, "quantity": quantity}],
        }
        response = await client.post(
            f"/api/v1/warehouse/{path}", headers=_headers(test_admin, key), json=payload
        )
        assert response.status_code == 201
    report = await client.get(
        "/api/v1/warehouse/reports/turnover", headers=_headers(test_admin)
    )
    assert report.status_code == 200
    row = report.json()["items"][0]
    assert Decimal(row["inbound_qty"]) == Decimal("10")
    assert Decimal(row["outbound_qty"]) == Decimal("3")
    assert Decimal(row["quantity"]) == Decimal("7")
