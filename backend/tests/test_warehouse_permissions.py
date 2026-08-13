"""Warehouse role permissions and warehouse-scope isolation."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, ROLE_PERMISSIONS, has_permission
from app.models.user import User, UserRole
from app.services.auth import create_access_token, get_password_hash
from tests.warehouse_fixtures import seed_two_warehouses


def _token(user: User) -> str:
    return create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role.value}
    )


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


def test_role_permission_matrix():
    admin_perms = ROLE_PERMISSIONS[UserRole.WAREHOUSE_ADMIN]
    keeper_perms = ROLE_PERMISSIONS[UserRole.COMPANY_STOREKEEPER]
    leader_perms = ROLE_PERMISSIONS[UserRole.COMPANY_LEADER]
    bidding_perms = ROLE_PERMISSIONS[UserRole.BIDDING]

    assert Permission.VIEW_ALL_WAREHOUSES in admin_perms
    assert Permission.CONFIRM_WAREHOUSE_COUNT in admin_perms
    assert Permission.VOID_WAREHOUSE_DOCUMENT in admin_perms
    assert Permission.MANAGE_WAREHOUSE_MATERIALS in admin_perms
    assert Permission.IMPORT_WAREHOUSE_DATA in admin_perms

    assert Permission.POST_WAREHOUSE_INBOUND in keeper_perms
    assert Permission.POST_WAREHOUSE_TRANSFER in keeper_perms
    assert Permission.ENTER_WAREHOUSE_COUNT in keeper_perms
    assert Permission.CONFIRM_WAREHOUSE_COUNT not in keeper_perms
    assert Permission.VOID_WAREHOUSE_DOCUMENT not in keeper_perms
    assert Permission.MANAGE_WAREHOUSE_MASTER not in keeper_perms
    assert Permission.VIEW_ALL_WAREHOUSES not in keeper_perms

    assert Permission.VIEW_WAREHOUSE_INVENTORY in leader_perms
    assert Permission.VIEW_ALL_WAREHOUSES in leader_perms
    assert Permission.POST_WAREHOUSE_INBOUND not in leader_perms

    assert Permission.VIEW_WAREHOUSE_INVENTORY not in bidding_perms


@pytest.mark.asyncio
async def test_storekeeper_cannot_read_unauthorized_warehouse(
    client: AsyncClient,
    test_db: AsyncSession,
    test_admin: User,
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    keeper = await _create_user(test_db, "keeper-scope", UserRole.COMPANY_STOREKEEPER)
    from app.models.warehouse import WarehouseUserScope

    test_db.add(
        WarehouseUserScope(user_id=keeper.id, warehouse_id=ctx.wh1.id, is_default=True)
    )
    await test_db.commit()

    headers = {"Authorization": f"Bearer {_token(keeper)}"}
    allowed = await client.get(
        f"/api/v1/warehouse/warehouses/{ctx.wh1.id}", headers=headers
    )
    denied = await client.get(
        f"/api/v1/warehouse/warehouses/{ctx.wh2.id}", headers=headers
    )
    balances = await client.get(
        "/api/v1/warehouse/stock-balances",
        headers=headers,
        params={"warehouse_id": ctx.wh2.id},
    )

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert balances.status_code == 403


@pytest.mark.asyncio
async def test_storekeeper_cannot_outbound_from_unauthorized_warehouse(
    client: AsyncClient,
    test_db: AsyncSession,
    test_admin: User,
):
    ctx = await seed_two_warehouses(test_db, test_admin)
    keeper = await _create_user(test_db, "keeper-post", UserRole.COMPANY_STOREKEEPER)
    from app.models.warehouse import WarehouseUserScope

    test_db.add(
        WarehouseUserScope(user_id=keeper.id, warehouse_id=ctx.wh1.id, is_default=True)
    )
    await test_db.commit()

    admin_headers = {"Authorization": f"Bearer {_token(test_admin)}"}
    inbound = await client.post(
        "/api/v1/warehouse/inbounds",
        headers={**admin_headers, "Idempotency-Key": "seed-in-1"},
        json={
            "warehouse_id": ctx.wh2.id,
            "location_id": ctx.loc2.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "admin",
            "business_type": "OPENING",
            "lines": [{"material_id": ctx.material.id, "quantity": "6"}],
        },
    )
    assert inbound.status_code == 201

    denied = await client.post(
        "/api/v1/warehouse/outbounds",
        headers={"Authorization": f"Bearer {_token(keeper)}", "Idempotency-Key": "bad-out"},
        json={
            "warehouse_id": ctx.wh2.id,
            "location_id": ctx.loc2.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "keeper",
            "business_type": "ISSUE",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert denied.status_code == 403
    assert denied.json()["error_code"] == "7002"


@pytest.mark.asyncio
async def test_leader_is_read_only(client: AsyncClient, test_db: AsyncSession, test_admin: User):
    ctx = await seed_two_warehouses(test_db, test_admin)
    leader = await _create_user(test_db, "leader-wh", UserRole.COMPANY_LEADER)
    headers = {"Authorization": f"Bearer {_token(leader)}"}

    listed = await client.get("/api/v1/warehouse/warehouses", headers=headers)
    posted = await client.post(
        "/api/v1/warehouse/inbounds",
        headers=headers,
        json={
            "warehouse_id": ctx.wh1.id,
            "location_id": ctx.loc1.id,
            "project_id": ctx.project_a.id,
            "occurred_on": "2026-08-13",
            "handler": "leader",
            "business_type": "PURCHASE",
            "lines": [{"material_id": ctx.material.id, "quantity": "1"}],
        },
    )
    assert listed.status_code == 200
    assert len(listed.json()) >= 2
    assert posted.status_code == 403


def test_admin_inherits_all_warehouse_permissions():
    admin = User(username="a", hashed_password="x", role=UserRole.ADMIN, is_superuser=False)
    assert has_permission(admin, Permission.VOID_WAREHOUSE_DOCUMENT)
    assert has_permission(admin, Permission.VIEW_WAREHOUSE_INVENTORY)
