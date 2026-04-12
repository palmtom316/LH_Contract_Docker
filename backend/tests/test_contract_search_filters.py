from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_upstream import ContractUpstream
from app.models.system import SysDictionary
from app.models.user import User
from app.routers import contract_search


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeExecuteResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _FakeScalarResult(self._rows)


class _FakeDb:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, _stmt):
        return _FakeExecuteResult(self._rows)


@pytest.mark.asyncio
async def test_expand_dictionary_filter_values_includes_value_and_label_variants():
    db = _FakeDb([
        SimpleNamespace(value="ENGINEERING", label="工程类合同"),
    ])

    values = await contract_search._expand_dictionary_filter_values(
        db,
        dictionary_category="contract_category",
        raw_value="ENGINEERING",
    )

    assert values == ["ENGINEERING", "ENGINEERING", "工程类合同"]


def test_build_multi_value_ilike_condition_deduplicates_case_insensitively():
    condition = contract_search._build_multi_value_ilike_condition(
        ContractUpstream.category,
        ["ENGINEERING", "engineering", "工程类合同"],
    )

    compiled = str(condition)
    assert compiled.count("lower(contracts_upstream.category) LIKE lower(") == 2


@pytest.mark.asyncio
async def test_upstream_query_accepts_dictionary_value_for_legacy_contract_category_and_company_category(
    client,
    test_db: AsyncSession,
    test_admin: User,
    admin_token: str,
):
    test_db.add_all([
        SysDictionary(
            category="contract_category",
            label="工程类合同",
            value="ENGINEERING",
            sort_order=1,
            is_active=True,
        ),
        SysDictionary(
            category="project_category",
            label="市政工程",
            value="MUNICIPAL",
            sort_order=1,
            is_active=True,
        ),
        ContractUpstream(
            serial_number=9910,
            contract_code="FILTER-UP-001",
            contract_name="筛选兼容合同",
            party_a_name="筛选甲方",
            party_b_name="筛选乙方",
            category="工程类合同",
            company_category="市政工程",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2026, 4, 1),
            status="执行中",
            created_by=test_admin.id,
        ),
    ])
    await test_db.commit()

    response = await client.get(
        "/api/v1/contracts/search/upstream-query",
        params={
            "contract_category": "ENGINEERING",
            "company_category": "MUNICIPAL",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["contract_code"] == "FILTER-UP-001"
