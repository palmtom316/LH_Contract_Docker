from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_upstream import ContractUpstream
from app.models.user import User


@pytest.fixture
def seeded_upstream_contract(event_loop, test_db: AsyncSession, test_admin: User):
    async def _seed():
        contract = ContractUpstream(
            serial_number=9601,
            contract_code="SUMMARY-UP-001",
            contract_name="摘要权限合同",
            party_a_name="摘要甲方",
            party_b_name="摘要乙方",
            category="工程类",
            contract_amount=Decimal("9000.00"),
            project_name="摘要项目",
            sign_date=date(2026, 2, 8),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)
        return contract

    return event_loop.run_until_complete(_seed())


@pytest.mark.asyncio
async def test_general_affairs_user_cannot_read_upstream_summary(client, general_affairs_token, seeded_upstream_contract):
    response = await client.get(
        f"/api/v1/contracts/upstream/{seeded_upstream_contract.id}/summary",
        headers={"Authorization": f"Bearer {general_affairs_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bidding_user_can_read_upstream_summary(client, user_token, seeded_upstream_contract):
    response = await client.get(
        f"/api/v1/contracts/upstream/{seeded_upstream_contract.id}/summary",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_code"] == "SUMMARY-UP-001"
