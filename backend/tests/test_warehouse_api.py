"""Warehouse HTTP API smoke tests."""

from datetime import date
from io import BytesIO

import pytest
from app.models.contract_upstream import ContractUpstream
from app.models.user import User
from app.services.auth import create_access_token
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from tests.warehouse_fixtures import seed_two_warehouses


async def _seed_upstream_contract(
    db: AsyncSession, admin: User, **overrides
) -> ContractUpstream:
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


@pytest.mark.asyncio
async def test_delete_unused_warehouse_and_location(
    client: AsyncClient, test_admin: User
):
    created = await client.post(
        "/api/v1/warehouse/warehouses",
        headers=_headers(test_admin),
        json={"code": "WH-DEL", "name": "待删库"},
    )
    assert created.status_code == 201
    warehouse = created.json()
    extra = await client.post(
        f"/api/v1/warehouse/warehouses/{warehouse['id']}/locations",
        headers=_headers(test_admin),
        json={"code": "A01", "name": "货架A"},
    )
    assert extra.status_code == 201
    deleted_location = await client.delete(
        f"/api/v1/warehouse/locations/{extra.json()['id']}",
        headers=_headers(test_admin),
    )
    assert deleted_location.status_code == 204
    deleted_warehouse = await client.delete(
        f"/api/v1/warehouse/warehouses/{warehouse['id']}",
        headers=_headers(test_admin),
    )
    assert deleted_warehouse.status_code == 204


@pytest.mark.asyncio
async def test_cannot_delete_warehouse_after_inbound(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "keep-wh"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": date.today().isoformat(),
            "handler": "admin",
            "business_type": "OWNER_SUPPLY",
            "delivery_note_file": "warehouse/2026/08/note.pdf",
            "delivery_note_file_name": "送货单.pdf",
            "lines": [{"material_id": ctx.material.id, "quantity": "1.5"}],
        },
    )
    assert inbound.status_code == 201
    assert inbound.json()["business_type"] == "OWNER_SUPPLY"
    assert inbound.json()["delivery_note_file_name"] == "送货单.pdf"
    assert inbound.json()["lines"][0]["material_unit"] == "圈"

    blocked = await client.delete(
        f"/api/v1/warehouse/warehouses/{ctx.wh1.id}",
        headers=_headers(test_admin),
    )
    assert blocked.status_code == 422


@pytest.mark.asyncio
async def test_scrap_disposal_requires_basis_file(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=_headers(test_admin, "scrap-in"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": date.today().isoformat(),
            "handler": "admin",
            "business_type": "PURCHASE",
            "lines": [{"material_id": ctx.material.id, "quantity": "4"}],
        },
    )
    assert inbound.status_code == 201

    missing = await client.post(
        "/api/v1/warehouse/outbounds",
        headers=_headers(test_admin, "scrap-missing"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": date.today().isoformat(),
            "handler": "admin",
            "business_type": "SCRAP_DISPOSAL",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert missing.status_code == 422

    posted = await client.post(
        "/api/v1/warehouse/outbounds",
        headers=_headers(test_admin, "scrap-ok"),
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": date.today().isoformat(),
            "handler": "admin",
            "business_type": "SCRAP_DISPOSAL",
            "scrap_basis_file": "warehouse/2026/08/scrap.pdf",
            "scrap_basis_file_name": "废旧处理审批.pdf",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert posted.status_code == 201
    assert posted.json()["business_type"] == "SCRAP_DISPOSAL"
    assert posted.json()["scrap_basis_file_name"] == "废旧处理审批.pdf"


@pytest.mark.asyncio
async def test_opening_import_template_and_post(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    ctx = await seed_two_warehouses(test_db, test_admin)

    template = await client.get(
        "/api/v1/warehouse/opening-entries/template.xlsx",
        headers=_headers(test_admin),
    )
    assert template.status_code == 200
    assert "spreadsheet" in template.headers.get("content-type", "")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "期初录入"
    sheet.append(
        [
            "物资编码",
            "物资名称",
            "厂家",
            "规格",
            "单位",
            "类别",
            "供应",
            "成色",
            "库房编码",
            "库房名称",
            "货位编码",
            "货位名称",
            "项目编码",
            "项目名称",
            "数量",
            "日期",
            "经办人",
            "备注",
        ]
    )
    sheet.append(
        [
            ctx.material.code,
            ctx.material.name,
            ctx.material.brand,
            ctx.material.specification,
            ctx.material.unit,
            "主材",
            "甲供",
            "新料",
            ctx.wh1.code,
            ctx.wh1.name,
            ctx.loc1.code,
            ctx.loc1.name,
            ctx.project_a.code,
            ctx.project_a.name,
            10,
            date.today().isoformat(),
            "期初管理员",
            "期初导入",
        ]
    )
    sheet.append(
        [
            ctx.material.code,
            ctx.material.name,
            ctx.material.brand,
            ctx.material.specification,
            ctx.material.unit,
            "主材",
            "甲供",
            "新料",
            ctx.wh2.code,
            ctx.wh2.name,
            ctx.loc2.code,
            ctx.loc2.name,
            ctx.project_b.code,
            ctx.project_b.name,
            4.5,
            date.today().isoformat(),
            "期初管理员",
            "第二批",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    result = await client.post(
        "/api/v1/warehouse/opening-entries/import",
        headers=_headers(test_admin),
        files={
            "file": (
                "opening.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert result.status_code == 200
    body = result.json()
    assert body["created_count"] == 2
    assert body["line_count"] == 2
    assert body["skipped_count"] == 0
    assert {doc["business_type"] for doc in body["documents"]} == {"OPENING"}

    stock = await client.get(
        "/api/v1/warehouse/stock-balances",
        headers=_headers(test_admin),
        params={"material_id": ctx.material.id, "include_zero": True},
    )
    assert stock.status_code == 200
    total = sum(float(item["quantity"]) for item in stock.json()["items"])
    assert total == 14.5


async def test_opening_import_auto_creates_material_archive(
    client: AsyncClient, test_db: AsyncSession, test_admin: User
):
    """期初录入留空物资编码时，按档案字段自动建档；重复幂等复用。"""
    ctx = await seed_two_warehouses(test_db, test_admin)

    headers_row = [
        "物资编码",
        "物资名称",
        "厂家",
        "规格",
        "单位",
        "类别",
        "供应",
        "成色",
        "库房编码",
        "库房名称",
        "货位编码",
        "货位名称",
        "项目编码",
        "项目名称",
        "数量",
        "日期",
        "经办人",
        "备注",
    ]

    def profile_row(name, brand, spec, unit, category, supply, condition, qty):
        return [
            "",
            name,
            brand,
            spec,
            unit,
            category,
            supply,
            condition,
            ctx.wh1.code,
            ctx.wh1.name,
            ctx.loc1.code,
            ctx.loc1.name,
            ctx.project_a.code,
            ctx.project_a.name,
            qty,
            date.today().isoformat(),
            "期初管理员",
            "自动建档",
        ]

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "期初录入"
    sheet.append(headers_row)
    # 行2：留空编码 + 全新档案 -> 自动建档（主材/乙供/新料）
    sheet.append(
        profile_row("光圆钢筋", "宝钢", "HPB300 φ8", "吨", "主材", "乙供", "新料", 5)
    )
    # 行3：同档案（留空编码）-> 复用行2自动建档的物资，不重复创建
    sheet.append(
        profile_row("光圆钢筋", "宝钢", "HPB300 φ8", "吨", "主材", "乙供", "新料", 3)
    )
    # 行4：留空编码但档案与预置物资（镀锌铁丝/示例厂/2.0mm/圈/主材/甲供/新料）一致 -> 按身份键复用
    sheet.append(
        profile_row("镀锌铁丝", "示例厂", "2.0mm", "圈", "主材", "甲供", "新料", 2)
    )

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    result = await client.post(
        "/api/v1/warehouse/opening-entries/import",
        headers=_headers(test_admin),
        files={
            "file": (
                "opening-autocreate.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert result.status_code == 200
    body = result.json()
    assert body["skipped_count"] == 0, body.get("errors")
    # 三行同一库房/货位/项目/日期/经办人 -> 合并为一张期初单
    assert body["created_count"] == 1
    assert body["line_count"] == 3

    # 档案只应有预置的「镀锌铁丝」+ 新建的「光圆钢筋」共 2 条
    materials = await client.get(
        "/api/v1/warehouse/materials",
        headers=_headers(test_admin),
        params={"q": "钢筋"},
    )
    assert materials.status_code == 200
    new_items = [m for m in materials.json() if m["name"] == "光圆钢筋"]
    assert len(new_items) == 1, "重复档案应被幂等复用，不应新建"
    new_material = new_items[0]
    assert new_material["code"].startswith("ZC-Y-"), new_material["code"]
    assert new_material["category"] == "ZC"
    assert new_material["supply_type"] == "Y"

    all_materials = await client.get(
        "/api/v1/warehouse/materials",
        headers=_headers(test_admin),
    )
    names = {m["name"] for m in all_materials.json()}
    assert names == {"镀锌铁丝", "光圆钢筋"}, names

    # 库存核对：新建物资 8（5+3），预置物资 2
    stock_new = await client.get(
        "/api/v1/warehouse/stock-balances",
        headers=_headers(test_admin),
        params={"material_id": new_material["id"], "include_zero": True},
    )
    assert stock_new.status_code == 200
    assert sum(float(i["quantity"]) for i in stock_new.json()["items"]) == 8

    stock_seed = await client.get(
        "/api/v1/warehouse/stock-balances",
        headers=_headers(test_admin),
        params={"material_id": ctx.material.id, "include_zero": True},
    )
    assert stock_seed.status_code == 200
    assert sum(float(i["quantity"]) for i in stock_seed.json()["items"]) == 2
