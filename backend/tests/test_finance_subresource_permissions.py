from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayable
from app.models.contract_management import ContractManagement, FinanceManagementPayable
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceivable
from app.models.user import User


@pytest.fixture
def seeded_upstream_receivable(event_loop, test_db: AsyncSession, test_admin: User):
    async def _seed():
        contract = ContractUpstream(
            serial_number=9501,
            contract_code="PERM-UP-001",
            contract_name="权限上游合同",
            party_a_name="甲方公司",
            party_b_name="乙方公司",
            category="工程类",
            company_category="主网",
            contract_amount=Decimal("5000.00"),
            sign_date=date(2026, 2, 1),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)

        receivable = FinanceUpstreamReceivable(
            contract_id=contract.id,
            category="进度款",
            amount=Decimal("1000.00"),
            description="首笔应收",
            expected_date=date(2026, 2, 5),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        )
        test_db.add(receivable)
        await test_db.commit()

        return {
            "contract_id": contract.id,
            "payload": {
                "contract_id": contract.id,
                "category": "尾款",
                "amount": "800.00",
                "description": "尾款应收",
                "expected_date": "2026-03-01",
            },
        }

    return event_loop.run_until_complete(_seed())


@pytest.fixture
def seeded_downstream_payable(event_loop, test_db: AsyncSession, test_admin: User):
    async def _seed():
        contract = ContractDownstream(
            serial_number=9502,
            contract_code="PERM-DS-001",
            contract_name="权限下游合同",
            party_a_name="我方公司",
            party_b_name="分包单位",
            category="工程类",
            contract_amount=Decimal("3000.00"),
            sign_date=date(2026, 2, 2),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)

        payable = FinanceDownstreamPayable(
            contract_id=contract.id,
            category="进度款",
            amount=Decimal("600.00"),
            description="首笔应付",
            expected_date=date(2026, 2, 6),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        )
        test_db.add(payable)
        await test_db.commit()

        return {"contract_id": contract.id}

    return event_loop.run_until_complete(_seed())


@pytest.fixture
def seeded_management_payable(event_loop, test_db: AsyncSession, test_admin: User):
    async def _seed():
        contract = ContractManagement(
            serial_number=9503,
            contract_code="PERM-MGMT-001",
            contract_name="权限管理合同",
            party_a_name="我方公司",
            party_b_name="管理单位",
            category="服务类",
            contract_amount=Decimal("2000.00"),
            sign_date=date(2026, 2, 3),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)

        payable = FinanceManagementPayable(
            contract_id=contract.id,
            category="服务费",
            amount=Decimal("400.00"),
            description="首笔应付",
            expected_date=date(2026, 2, 7),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        )
        test_db.add(payable)
        await test_db.commit()

        return {"contract_id": contract.id}

    return event_loop.run_until_complete(_seed())


@pytest.mark.asyncio
async def test_bidding_user_cannot_list_upstream_receivables(client, user_token, seeded_upstream_receivable):
    response = await client.get(
        f"/api/v1/contracts/upstream/{seeded_upstream_receivable['contract_id']}/receivables",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bidding_user_cannot_create_upstream_receivable(client, user_token, seeded_upstream_receivable):
    response = await client.post(
        f"/api/v1/contracts/upstream/{seeded_upstream_receivable['contract_id']}/receivables",
        json=seeded_upstream_receivable["payload"],
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bidding_user_cannot_list_downstream_payables(client, user_token, seeded_downstream_payable):
    response = await client.get(
        f"/api/v1/contracts/downstream/{seeded_downstream_payable['contract_id']}/payables",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bidding_user_cannot_list_management_payables(client, user_token, seeded_management_payable):
    response = await client.get(
        f"/api/v1/contracts/management/{seeded_management_payable['contract_id']}/payables",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_finance_user_can_list_downstream_payables(client, finance_token, seeded_downstream_payable):
    response = await client.get(
        f"/api/v1/contracts/downstream/{seeded_downstream_payable['contract_id']}/payables",
        headers={"Authorization": f"Bearer {finance_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_general_affairs_user_can_list_management_payables(client, general_affairs_token, seeded_management_payable):
    response = await client.get(
        f"/api/v1/contracts/management/{seeded_management_payable['contract_id']}/payables",
        headers={"Authorization": f"Bearer {general_affairs_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
