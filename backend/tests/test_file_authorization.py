"""
Focused file authorization tests for business-backed attachments.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract_downstream import ContractDownstream
from app.models.contract_upstream import ContractUpstream
from app.models.expense import ExpenseNonContract
from app.models.user import User, UserRole
from app.services.file_authorization import user_can_access_file_path


async def _create_user(
    db: AsyncSession,
    *,
    username: str,
    role: UserRole,
    is_superuser: bool = False,
) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="not-used",
        role=role,
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_upstream_contract_file_allows_matching_view_permission(test_db: AsyncSession):
    viewer = await _create_user(test_db, username="bidding-viewer", role=UserRole.BIDDING)
    contract = ContractUpstream(
        contract_code="UP-ACCESS-001",
        contract_name="Upstream Attachment",
        party_a_name="甲方",
        party_b_name="乙方",
        contract_file_key="contracts/2026/04/upstream-contract.pdf",
    )
    test_db.add(contract)
    await test_db.commit()

    allowed = await user_can_access_file_path(
        "contracts/2026/04/upstream-contract.pdf",
        test_db,
        viewer,
    )

    assert allowed is True


@pytest.mark.asyncio
async def test_downstream_contract_file_denies_user_without_matching_permission(test_db: AsyncSession):
    viewer = await _create_user(test_db, username="upstream-only", role=UserRole.BIDDING)
    contract = ContractDownstream(
        contract_code="DOWN-ACCESS-001",
        contract_name="Downstream Attachment",
        party_a_name="甲方",
        party_b_name="乙方",
        contract_file_key="contracts/2026/04/downstream-contract.pdf",
    )
    test_db.add(contract)
    await test_db.commit()

    allowed = await user_can_access_file_path(
        "contracts/2026/04/downstream-contract.pdf",
        test_db,
        viewer,
    )

    assert allowed is False


@pytest.mark.asyncio
async def test_expense_file_respects_owner_scope_for_limited_roles(test_db: AsyncSession):
    owner = await _create_user(test_db, username="expense-owner", role=UserRole.BIDDING)
    outsider = await _create_user(test_db, username="expense-outsider", role=UserRole.BIDDING)
    finance = await _create_user(test_db, username="expense-finance", role=UserRole.FINANCE)

    expense = ExpenseNonContract(
        expense_code="EXP-ACCESS-001",
        category="公司费用",
        amount=100,
        expense_date=date(2026, 4, 11),
        file_key="expenses/2026/04/receipt.pdf",
        created_by=owner.id,
        updated_by=owner.id,
    )
    test_db.add(expense)
    await test_db.commit()

    owner_allowed = await user_can_access_file_path("expenses/2026/04/receipt.pdf", test_db, owner)
    outsider_allowed = await user_can_access_file_path("expenses/2026/04/receipt.pdf", test_db, outsider)
    finance_allowed = await user_can_access_file_path("expenses/2026/04/receipt.pdf", test_db, finance)

    assert owner_allowed is True
    assert outsider_allowed is False
    assert finance_allowed is True
