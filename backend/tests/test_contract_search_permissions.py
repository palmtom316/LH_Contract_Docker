from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.models.contract_upstream import ContractUpstream
from app.models.expense import ExpenseNonContract
from app.models.user import User


@pytest.fixture
def seeded_contract_graph(event_loop, test_db: AsyncSession, test_admin: User):
    async def _seed():
        upstream = ContractUpstream(
            serial_number=9401,
            contract_code="SEARCH-PERM-UP-001",
            contract_name="SEARCH-PERM 上游合同",
            party_a_name="权限甲方",
            party_b_name="权限乙方",
            company_category="市区配网",
            category="工程类",
            contract_amount=Decimal("5000.00"),
            sign_date=date(2026, 1, 10),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add(upstream)
        await test_db.commit()
        await test_db.refresh(upstream)

        downstream = ContractDownstream(
            serial_number=9402,
            contract_code="SEARCH-PERM-DS-001",
            contract_name="SEARCH-PERM 下游合同",
            party_a_name="我方公司",
            party_b_name="管理乙方",
            upstream_contract_id=upstream.id,
            contract_amount=Decimal("1200.00"),
            sign_date=date(2026, 1, 11),
            status="执行中",
            created_by=test_admin.id,
        )
        management = ContractManagement(
            serial_number=9403,
            contract_code="SEARCH-PERM-MGMT-001",
            contract_name="SEARCH-PERM 管理合同",
            party_a_name="我方公司",
            party_b_name="管理乙方",
            upstream_contract_id=upstream.id,
            contract_amount=Decimal("600.00"),
            sign_date=date(2026, 1, 12),
            status="执行中",
            created_by=test_admin.id,
        )
        expense = ExpenseNonContract(
            expense_code="SEARCH-PERM-EXP-001",
            attribution="PROJECT",
            category="项目费用",
            expense_type="MANAGEMENT",
            amount=Decimal("88.00"),
            expense_date=date(2026, 1, 13),
            upstream_contract_id=upstream.id,
            description="权限测试费用",
            created_by=test_admin.id,
        )
        test_db.add_all([downstream, management, expense])
        await test_db.commit()

        return {
            "upstream_id": upstream.id,
            "downstream_code": downstream.contract_code,
            "management_code": management.contract_code,
        }

    return event_loop.run_until_complete(_seed())


@pytest.mark.asyncio
async def test_bidding_user_search_cannot_see_downstream_management_or_expenses(
    client, user_token, seeded_contract_graph
):
    response = await client.get(
        "/api/v1/contracts/search",
        params={"query": "SEARCH-PERM"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"]
    assert data["results"][0]["downstream_contracts"] == []
    assert data["results"][0]["management_contracts"] == []
    assert data["results"][0]["expenses_by_category"] == []
    assert data["downstream_results"] == []
    assert data["management_results"] == []


@pytest.mark.asyncio
async def test_general_affairs_user_party_b_search_only_returns_management_matches(
    client, general_affairs_token, seeded_contract_graph
):
    response = await client.get(
        "/api/v1/contracts/search",
        params={"party_b_name": "管理乙方"},
        headers={"Authorization": f"Bearer {general_affairs_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["downstream_results"] == []
    assert len(data["management_results"]) == 1
