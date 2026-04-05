"""
Dictionary safety tests for referenced values.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.contract_upstream import ContractUpstream
from app.models.expense import ExpenseNonContract
from app.models.system import SysDictionary
from app.models.user import User, UserRole
from app.routers.system import OptionUpdate, delete_option, update_option
from app.services.auth import get_password_hash
from app.services.expense_service import ExpenseService


TEST_TABLES = [
    User.__table__,
    ContractUpstream.__table__,
    SysDictionary.__table__,
    ExpenseNonContract.__table__,
]


@pytest_asyncio.fixture
async def dictionary_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("ValidPass123"),
            full_name="Admin",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True,
        )
        session.add(admin)
        await session.flush()

        dictionary = SysDictionary(
            category="expense_type",
            label="管理费",
            value="管理费",
            sort_order=1,
            is_active=True,
        )
        session.add(dictionary)
        session.add(
            ExpenseNonContract(
                expense_code="EXP-DICT-001",
                attribution="COMPANY",
                category="公司费用",
                expense_type="管理费",
                amount=Decimal("100.00"),
                expense_date=date(2026, 4, 1),
                description="历史费用",
                created_by=admin.id,
                updated_by=admin.id,
            )
        )
        await session.commit()
        await session.refresh(admin)
        await session.refresh(dictionary)
        yield session, admin, dictionary

    await engine.dispose()


@pytest.mark.asyncio
async def test_cannot_delete_expense_type_dictionary_value_when_referenced(dictionary_db):
    session, admin, dictionary = dictionary_db

    result = await delete_option(dictionary.id, db=session, current_user=admin)

    await session.refresh(dictionary)
    assert result["deletion_mode"] == "disabled"
    assert dictionary.is_active is False


@pytest.mark.asyncio
async def test_can_disable_dictionary_value_without_breaking_existing_expense_reads(dictionary_db):
    session, admin, dictionary = dictionary_db

    await update_option(
        dictionary.id,
        OptionUpdate(is_active=False),
        db=session,
        current_user=admin,
    )

    service = ExpenseService(session)
    payload = await service.list_expenses(page=1, page_size=10, expense_type="管理费", current_user=admin)

    assert payload["total"] == 1
    assert payload["items"][0].expense_type == "管理费"


@pytest.mark.asyncio
async def test_existing_expense_records_render_when_dictionary_label_changes(dictionary_db):
    session, admin, dictionary = dictionary_db

    await update_option(
        dictionary.id,
        OptionUpdate(label="管理费（新标签）"),
        db=session,
        current_user=admin,
    )

    service = ExpenseService(session)
    payload = await service.list_expenses(page=1, page_size=10, expense_type="管理费", current_user=admin)

    assert payload["total"] == 1
    assert payload["items"][0].expense_type == "管理费"
