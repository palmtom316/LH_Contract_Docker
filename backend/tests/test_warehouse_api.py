"""Warehouse HTTP API smoke tests."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_upstream import ContractUpstream
from app.models.user import User
from app.services.auth import create_access_token
from tests.warehouse_fixtures import seed_two_warehouses


async def _seed_upstream_contract(db: AsyncSession, admin: User, **overrides) -> ContractUpstream:
    payload = {
        "serial_number": 101,
        "contract_code": "S-2026-08-101",
        "contract_name": "示范变电站改造工程",
        "party_a_name": "示例供电公司",
        "party_b_name": "示例施工方",
        "company_category": "主网工程",
        "created_by": admin.id,
    }
    payload.update(overrides)
    contract = ContractUpstream(**payload)
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


def _headers(user: User, key: str | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'username': user.username, 'role': user.role.value})}"
    }
    if key:
        headers["Idempotency-Key"] = key
    return headers


@pytest.mark.asyncio
async def test_master_data_and_inbound_flow(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    created = await client.post(
        "/api/v1/warehouse/warehouses",
        headers=_headers(test_admin),
        json={"code": "WH-A", "name": "材料总库", "address": "一号院"},
    )
    assert created.status_code == 201
    warehouse = created.json()
    assert any(loc["code"] == "STAGING" for loc in warehouse["locations"])

    contract = await _seed_upstream_contract(test_db, test_admin)
    project = await client.post(
        "/api/v1/warehouse/projects",
        headers=_headers(test_admin),
        json={"upstream_contract_id": contract.id},
    )
    assert project.status_code == 201
    assert project.json()["code"] == "101"
    assert project.json()["name"] == "示范变电站改造工程"
    assert project.json()["company_category"] == "主网工程"
    assert project.json()["party_a_name"] == "示例供电公司"

    material = await client.post(
        "/api/v1/warehouse/materials",
        headers=_headers(test_admin),
        json={
            "category": "ZC",
            "supply_type": "J",
            "condition": "NEW",
            "name": "电缆",
            "brand": "远东",
            "specification": "YJV-4x25",
            "unit": "米",
        },
    )
    assert material.status_code == 201
    assert material.json()["code"] == "ZC-J-001"

    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "api-in-1"),
        json={
            "warehouse_id": warehouse["id"],
            "location_id": warehouse["locations"][0]["id"],
            "project_id": project.json()["id"],
            "occurred_on": date.today().isoformat(),
            "handler": "库管",
            "business_type": "PURCHASE",
            "lines": [{"material_id": material.json()["id"], "quantity": "12.5"}],
        },
    )
    assert inbound.status_code == 201
    assert inbound.json()["document_no"].startswith("IN-")
    assert inbound.json()["status"] == "POSTED"

    stock = await client.get(
        "/api/v1/warehouse/stock-balances",
        headers=_headers(test_admin),
        params={"material_id": material.json()["id"]},
    )
    assert stock.status_code == 200
    assert float(stock.json()["items"][0]["quantity"]) == 12.5

    qr = await client.get(
        f"/api/v1/warehouse/materials/{material.json()['id']}/qr",
        headers=_headers(test_admin),
    )
    assert qr.status_code == 200
    assert "/m/warehouse/materials/" in qr.json()["payload"]
    assert "12.5" not in qr.json()["payload"]


@pytest.mark.asyncio
async def test_count_confirm_posts_once(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "count-in"),
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
    assert count["lines"]
    updated = await client.put(
        f"/api/v1/warehouse/counts/{count['id']}/lines",
        headers=_headers(test_admin),
        json={"lines": [{"id": count["lines"][0]["id"], "counted_quantity": "9"}]},
    )
    assert updated.status_code == 200
    confirmed = await client.post(
        f"/api/v1/warehouse/counts/{count['id']}/confirm",
        headers=_headers(test_admin),
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"
    second = await client.post(
        f"/api/v1/warehouse/counts/{count['id']}/confirm",
        headers=_headers(test_admin),
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_project_lookup_by_serial_and_name(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    await _seed_upstream_contract(
        test_db,
        test_admin,
        serial_number=88,
        contract_code="S-2026-08-088",
        contract_name="城南线路迁改工程",
        party_a_name="城南供电公司",
        company_category="配网工程",
    )

    by_serial = await client.get(
        "/api/v1/warehouse/upstream-contracts",
        headers=_headers(test_admin),
        params={"serial_number": 88},
    )
    assert by_serial.status_code == 200
    assert by_serial.json()[0]["contract_name"] == "城南线路迁改工程"
    assert by_serial.json()[0]["party_a_name"] == "城南供电公司"

    by_name = await client.get(
        "/api/v1/warehouse/upstream-contracts",
        headers=_headers(test_admin),
        params={"q": "线路迁改"},
    )
    assert by_name.status_code == 200
    assert by_name.json()[0]["serial_number"] == 88

    created = await client.post(
        "/api/v1/warehouse/projects",
        headers=_headers(test_admin),
        json={"code": "88"},
    )
    assert created.status_code == 201
    assert created.json()["code"] == "88"
    assert created.json()["name"] == "城南线路迁改工程"
    assert created.json()["company_category"] == "配网工程"

    listed = await client.get(
        "/api/v1/warehouse/projects",
        headers=_headers(test_admin),
        params={"q": "城南"},
    )
    assert listed.status_code == 200
    assert listed.json()[0]["party_a_name"] == "城南供电公司"
