"""
Downstream → Upstream Allocation Tests
Covers the bulk replace flow, strong balance validation, and upstream cost-allocation read.
"""
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.contract_upstream import ContractUpstream
from app.models.contract_downstream import ContractDownstream, DownstreamUpstreamAllocation
from app.models.user import User
from app.services.contract_downstream_service import ContractDownstreamService
from app.schemas.contract_downstream import AllocationCreate
from app.core.errors import ValidationError


async def _make_upstream(db: AsyncSession, user: User, code: str, name: str) -> ContractUpstream:
    u = ContractUpstream(
        contract_code=code,
        contract_name=name,
        party_a_name="A",
        party_b_name="B",
        category="工程类",
        contract_amount=Decimal("0"),
        sign_date=date(2026, 1, 1),
        status="执行中",
        created_by=user.id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _make_downstream(
    db: AsyncSession, user: User, amount: Decimal, code: str = "DS-001"
) -> ContractDownstream:
    d = ContractDownstream(
        contract_code=code,
        contract_name="测试下游合同",
        party_a_name="我方",
        party_b_name="供应商",
        category="货物类",
        contract_amount=amount,
        sign_date=date(2026, 1, 1),
        status="执行中",
        created_by=user.id,
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


@pytest.mark.asyncio
class TestDownstreamAllocations:
    async def test_replace_with_balanced_amounts_succeeds(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        u2 = await _make_upstream(test_db, test_admin, "US-2", "上游2")
        u3 = await _make_upstream(test_db, test_admin, "US-3", "上游3")
        d = await _make_downstream(test_db, test_admin, Decimal("1000.00"))

        service = ContractDownstreamService(test_db)
        items = [
            AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("100.00")),
            AllocationCreate(upstream_contract_id=u2.id, amount=Decimal("600.00")),
            AllocationCreate(upstream_contract_id=u3.id, amount=Decimal("300.00")),
        ]
        result = await service.replace_allocations(d.id, items, test_admin)

        assert len(result) == 3
        assert sum(a.amount for a in result) == Decimal("1000.00")

        listed = await service.list_allocations(d.id)
        assert len(listed) == 3

    async def test_replace_with_unbalanced_amounts_fails(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        u2 = await _make_upstream(test_db, test_admin, "US-2", "上游2")
        d = await _make_downstream(test_db, test_admin, Decimal("1000.00"))

        service = ContractDownstreamService(test_db)
        items = [
            AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("100.00")),
            AllocationCreate(upstream_contract_id=u2.id, amount=Decimal("600.00")),
        ]  # sum = 700, contract = 1000

        with pytest.raises(ValidationError) as exc_info:
            await service.replace_allocations(d.id, items, test_admin)
        assert "不一致" in str(exc_info.value.message)

    async def test_replace_with_duplicate_upstream_fails(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        d = await _make_downstream(test_db, test_admin, Decimal("500.00"))

        service = ContractDownstreamService(test_db)
        items = [
            AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("200.00")),
            AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("300.00")),
        ]

        with pytest.raises(ValidationError) as exc_info:
            await service.replace_allocations(d.id, items, test_admin)
        assert "重复" in str(exc_info.value.message)

    async def test_replace_with_unknown_upstream_fails(
        self, test_db: AsyncSession, test_admin: User
    ):
        d = await _make_downstream(test_db, test_admin, Decimal("500.00"))

        service = ContractDownstreamService(test_db)
        items = [AllocationCreate(upstream_contract_id=999999, amount=Decimal("500.00"))]

        with pytest.raises(ValidationError) as exc_info:
            await service.replace_allocations(d.id, items, test_admin)
        assert "不存在" in str(exc_info.value.message)

    async def test_replace_atomically_replaces_existing(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        u2 = await _make_upstream(test_db, test_admin, "US-2", "上游2")
        d = await _make_downstream(test_db, test_admin, Decimal("1000.00"))

        service = ContractDownstreamService(test_db)
        # 第一次：100 / 900
        await service.replace_allocations(
            d.id,
            [
                AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("100.00")),
                AllocationCreate(upstream_contract_id=u2.id, amount=Decimal("900.00")),
            ],
            test_admin,
        )
        # 第二次：400 / 600（应原子替换，旧的 100/900 必须被清掉）
        await service.replace_allocations(
            d.id,
            [
                AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("400.00")),
                AllocationCreate(upstream_contract_id=u2.id, amount=Decimal("600.00")),
            ],
            test_admin,
        )

        listed = await service.list_allocations(d.id)
        amounts = sorted(a.amount for a in listed)
        assert amounts == [Decimal("400.00"), Decimal("600.00")]

    async def test_clear_allocations_removes_all(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        d = await _make_downstream(test_db, test_admin, Decimal("100.00"))

        service = ContractDownstreamService(test_db)
        await service.replace_allocations(
            d.id,
            [AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("100.00"))],
            test_admin,
        )

        await service.clear_allocations(d.id, test_admin)
        assert await service.list_allocations(d.id) == []

    async def test_cascade_delete_when_downstream_removed(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        d = await _make_downstream(test_db, test_admin, Decimal("500.00"))

        service = ContractDownstreamService(test_db)
        await service.replace_allocations(
            d.id,
            [AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("500.00"))],
            test_admin,
        )
        d_id = d.id

        await test_db.delete(d)
        await test_db.commit()

        remaining = (
            await test_db.execute(
                select(DownstreamUpstreamAllocation).where(
                    DownstreamUpstreamAllocation.downstream_contract_id == d_id
                )
            )
        ).scalars().all()
        assert remaining == []

    async def test_upstream_cost_allocations_query(
        self, test_db: AsyncSession, test_admin: User
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        d_a = await _make_downstream(test_db, test_admin, Decimal("100.00"), code="DS-A")
        d_b = await _make_downstream(test_db, test_admin, Decimal("200.00"), code="DS-B")

        service = ContractDownstreamService(test_db)
        await service.replace_allocations(
            d_a.id,
            [AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("100.00"))],
            test_admin,
        )
        await service.replace_allocations(
            d_b.id,
            [AllocationCreate(upstream_contract_id=u1.id, amount=Decimal("200.00"))],
            test_admin,
        )

        rows = await service.list_upstream_cost_allocations(u1.id)
        assert len(rows) == 2
        codes = {r["downstream_contract_code"] for r in rows}
        assert codes == {"DS-A", "DS-B"}
        total = sum(r["amount"] for r in rows)
        assert total == Decimal("300.00")


@pytest.mark.asyncio
class TestAllocationApiEndpoints:
    async def test_put_endpoint_validates_balance(
        self, client, test_db, test_admin, admin_token
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        d = await _make_downstream(test_db, test_admin, Decimal("1000.00"))

        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.put(
            f"/api/v1/contracts/downstream/{d.id}/allocations",
            headers=headers,
            json={
                "allocations": [
                    {"upstream_contract_id": u1.id, "amount": "500.00"}
                ]
            },
        )
        assert resp.status_code == 422

    async def test_put_then_get_roundtrip(
        self, client, test_db, test_admin, admin_token
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        u2 = await _make_upstream(test_db, test_admin, "US-2", "上游2")
        d = await _make_downstream(test_db, test_admin, Decimal("300.00"))

        headers = {"Authorization": f"Bearer {admin_token}"}
        put_resp = await client.put(
            f"/api/v1/contracts/downstream/{d.id}/allocations",
            headers=headers,
            json={
                "allocations": [
                    {"upstream_contract_id": u1.id, "amount": "100.00"},
                    {"upstream_contract_id": u2.id, "amount": "200.00"},
                ]
            },
        )
        assert put_resp.status_code == 200, put_resp.text

        get_resp = await client.get(
            f"/api/v1/contracts/downstream/{d.id}/allocations", headers=headers
        )
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert len(body) == 2

    async def test_upstream_cost_allocations_endpoint(
        self, client, test_db, test_admin, admin_token
    ):
        u1 = await _make_upstream(test_db, test_admin, "US-1", "上游1")
        d = await _make_downstream(test_db, test_admin, Decimal("250.00"))

        headers = {"Authorization": f"Bearer {admin_token}"}
        await client.put(
            f"/api/v1/contracts/downstream/{d.id}/allocations",
            headers=headers,
            json={
                "allocations": [
                    {"upstream_contract_id": u1.id, "amount": "250.00"}
                ]
            },
        )

        resp = await client.get(
            f"/api/v1/contracts/upstream/{u1.id}/cost-allocations", headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["downstream_contract_code"] == "DS-001"
        assert Decimal(body[0]["amount"]) == Decimal("250.00")
