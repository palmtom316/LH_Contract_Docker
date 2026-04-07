"""
Upgrade safety regression tests for long-running production data.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.audit_log import AuditLog
from app.models.contract_downstream import ContractDownstream
from app.models.contract_management import ContractManagement
from app.models.contract_upstream import ContractUpstream
from app.models.expense import ExpenseNonContract
from app.models.refresh_token import RefreshToken
from app.models.system import SysDictionary
from app.models.user import User


async def _count_rows(db: AsyncSession, model) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar_one()


@pytest.mark.asyncio
async def test_existing_expense_records_remain_queryable_after_upgrade(
    client: AsyncClient,
    test_db: AsyncSession,
    test_admin: User,
    admin_token: str,
):
    expense = ExpenseNonContract(
        expense_code="EXP-UPGRADE-001",
        attribution="PROJECT",
        category="项目费用",
        expense_type="历史管理费",
        amount=Decimal("1250.00"),
        expense_date=date(2026, 3, 15),
        description="升级前已录入费用",
        created_by=test_admin.id,
        updated_by=test_admin.id,
    )
    test_db.add(expense)
    await test_db.commit()

    response = await client.get(
        "/api/v1/expenses/",
        params={"expense_type": "历史管理费"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["expense_code"] == "EXP-UPGRADE-001"
    assert payload["items"][0]["expense_type"] == "历史管理费"


@pytest.mark.asyncio
async def test_existing_dictionary_values_remain_renderable_after_upgrade(
    client: AsyncClient,
    test_db: AsyncSession,
    test_admin: User,
    admin_token: str,
):
    legacy_value = "历史差旅费"
    test_db.add(
        SysDictionary(
            category="expense_type",
            label=legacy_value,
            value=legacy_value,
            sort_order=99,
            is_active=False,
            description="升级后停用，但历史记录仍需展示",
        )
    )
    expense = ExpenseNonContract(
        expense_code="EXP-UPGRADE-002",
        attribution="PROJECT",
        category="项目费用",
        expense_type=legacy_value,
        amount=Decimal("88.00"),
        expense_date=date(2026, 2, 10),
        description="历史字典值兼容验证",
        created_by=test_admin.id,
        updated_by=test_admin.id,
    )
    test_db.add(expense)
    await test_db.commit()
    await test_db.refresh(expense)

    response = await client.get(
        f"/api/v1/expenses/{expense.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["expense_type"] == legacy_value
    assert payload["description"] == "历史字典值兼容验证"


@pytest.mark.asyncio
async def test_legacy_upload_paths_remain_downloadable_after_upgrade(
    client: AsyncClient,
    admin_token: str,
    tmp_path,
):
    original_upload_dir = settings.UPLOAD_DIR
    legacy_relative_path = "legacy/contracts/2025/scan.pdf"
    expected_bytes = b"legacy-upload-payload"

    try:
        settings.UPLOAD_DIR = str(tmp_path)
        local_file = tmp_path / legacy_relative_path
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(expected_bytes)

        response = await client.get(
            f"/api/v1/common/files/{legacy_relative_path}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.content == expected_bytes
    finally:
        settings.UPLOAD_DIR = original_upload_dir


@pytest.mark.asyncio
async def test_refresh_token_and_login_upgrade_do_not_modify_business_data(
    client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
):
    test_db.add(
        SysDictionary(
            category="expense_type",
            label="管理费",
            value="管理费",
            sort_order=1,
            is_active=True,
        )
    )
    test_db.add(
        ExpenseNonContract(
            expense_code="EXP-UPGRADE-003",
            attribution="COMPANY",
            category="公司费用",
            expense_type="管理费",
            amount=Decimal("300.00"),
            expense_date=date(2026, 4, 1),
            description="登录刷新前业务数据",
            created_by=test_user.id,
            updated_by=test_user.id,
        )
    )
    await test_db.commit()

    before_counts = {
        "upstream_contracts": await _count_rows(test_db, ContractUpstream),
        "downstream_contracts": await _count_rows(test_db, ContractDownstream),
        "management_contracts": await _count_rows(test_db, ContractManagement),
        "expenses": await _count_rows(test_db, ExpenseNonContract),
        "dictionaries": await _count_rows(test_db, SysDictionary),
        "users": await _count_rows(test_db, User),
        "audit_logs": await _count_rows(test_db, AuditLog),
        "refresh_tokens": await _count_rows(test_db, RefreshToken),
    }

    login_response = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200

    after_counts = {
        "upstream_contracts": await _count_rows(test_db, ContractUpstream),
        "downstream_contracts": await _count_rows(test_db, ContractDownstream),
        "management_contracts": await _count_rows(test_db, ContractManagement),
        "expenses": await _count_rows(test_db, ExpenseNonContract),
        "dictionaries": await _count_rows(test_db, SysDictionary),
        "users": await _count_rows(test_db, User),
        "audit_logs": await _count_rows(test_db, AuditLog),
        "refresh_tokens": await _count_rows(test_db, RefreshToken),
    }

    assert after_counts["upstream_contracts"] == before_counts["upstream_contracts"]
    assert after_counts["downstream_contracts"] == before_counts["downstream_contracts"]
    assert after_counts["management_contracts"] == before_counts["management_contracts"]
    assert after_counts["expenses"] == before_counts["expenses"]
    assert after_counts["dictionaries"] == before_counts["dictionaries"]
    assert after_counts["users"] == before_counts["users"]
    assert after_counts["audit_logs"] == before_counts["audit_logs"] + 1
    assert after_counts["refresh_tokens"] == before_counts["refresh_tokens"] + 2
