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
def seeded_multi_upstream_search_graph(event_loop, test_db: AsyncSession, test_admin: User):
    async def _seed():
        upstream_a = ContractUpstream(
            serial_number=9701,
            contract_code="BATCH-UP-001",
            contract_name="批量查询上游一",
            party_a_name="甲方一",
            party_b_name="乙方一",
            category="工程类",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2026, 3, 1),
            status="执行中",
            created_by=test_admin.id,
        )
        upstream_b = ContractUpstream(
            serial_number=9702,
            contract_code="BATCH-UP-002",
            contract_name="批量查询上游二",
            party_a_name="甲方二",
            party_b_name="乙方二",
            category="工程类",
            contract_amount=Decimal("2000.00"),
            sign_date=date(2026, 3, 2),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add_all([upstream_a, upstream_b])
        await test_db.commit()
        await test_db.refresh(upstream_a)
        await test_db.refresh(upstream_b)

        test_db.add_all([
            ContractDownstream(
                serial_number=9703,
                contract_code="BATCH-DS-001",
                contract_name="批量下游一",
                party_a_name="我方公司",
                party_b_name="分包一",
                upstream_contract_id=upstream_a.id,
                contract_amount=Decimal("300.00"),
                sign_date=date(2026, 3, 3),
                status="执行中",
                created_by=test_admin.id,
            ),
            ContractManagement(
                serial_number=9704,
                contract_code="BATCH-MGMT-001",
                contract_name="批量管理一",
                party_a_name="我方公司",
                party_b_name="管理一",
                upstream_contract_id=upstream_a.id,
                contract_amount=Decimal("120.00"),
                sign_date=date(2026, 3, 4),
                status="执行中",
                created_by=test_admin.id,
            ),
            ExpenseNonContract(
                expense_code="BATCH-EXP-001",
                attribution="PROJECT",
                category="项目费用",
                expense_type="MANAGEMENT",
                amount=Decimal("66.00"),
                expense_date=date(2026, 3, 5),
                upstream_contract_id=upstream_b.id,
                description="批量查询费用",
                created_by=test_admin.id,
            ),
        ])
        await test_db.commit()

    event_loop.run_until_complete(_seed())


@pytest.mark.asyncio
async def test_search_keeps_nested_results_shape_after_batch_loading(client, admin_token, seeded_multi_upstream_search_graph):
    response = await client.get(
        "/api/v1/contracts/search",
        params={"query": "BATCH-UP"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2

    results_by_code = {item["contract_code"]: item for item in data["results"]}
    assert len(results_by_code["BATCH-UP-001"]["downstream_contracts"]) == 1
    assert len(results_by_code["BATCH-UP-001"]["management_contracts"]) == 1
    assert results_by_code["BATCH-UP-002"]["expenses_by_category"] == [
        {"category": "管理费", "amount": 66.0}
    ]


@pytest.mark.asyncio
async def test_companies_endpoint_returns_distinct_sorted_names(client, admin_token, test_db: AsyncSession, test_admin: User):
    upstream = ContractUpstream(
        serial_number=9801,
        contract_code="COMPANY-UP-001",
        contract_name="公司联想上游",
        party_a_name="重复公司",
        party_b_name="上游乙方",
        category="工程类",
        contract_amount=Decimal("100.00"),
        sign_date=date(2026, 3, 6),
        status="执行中",
        created_by=test_admin.id,
    )
    downstream = ContractDownstream(
        serial_number=9802,
        contract_code="COMPANY-DS-001",
        contract_name="公司联想下游",
        party_a_name="重复公司",
        party_b_name="分包公司",
        contract_amount=Decimal("100.00"),
        sign_date=date(2026, 3, 6),
        status="执行中",
        created_by=test_admin.id,
    )
    management = ContractManagement(
        serial_number=9803,
        contract_code="COMPANY-MGMT-001",
        contract_name="公司联想管理",
        party_a_name="管理甲方",
        party_b_name="重复公司",
        contract_amount=Decimal("100.00"),
        sign_date=date(2026, 3, 6),
        status="执行中",
        created_by=test_admin.id,
    )
    test_db.add_all([upstream, downstream, management])
    await test_db.commit()

    response = await client.get(
        "/api/v1/common/companies",
        params={"query": "重复"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == ["重复公司"]
