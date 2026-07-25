from datetime import date
from types import SimpleNamespace

import pytest

from app.services.contract_code_generator import ContractCodeGenerator


class _ScalarResult:
    def scalar_one_or_none(self):
        return "S-2026-07-009"


class _FakeDb:
    def __init__(self):
        self.calls = []

    def get_bind(self):
        return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    async def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        return _ScalarResult()


@pytest.mark.asyncio
async def test_postgresql_code_generation_takes_transaction_advisory_lock_first():
    db = _FakeDb()

    code = await ContractCodeGenerator(db).generate_upstream_code(date(2026, 7, 1))

    assert code == "S-2026-07-010"
    assert "pg_advisory_xact_lock" in db.calls[0][0]
    assert db.calls[0][1] == {"lock_key": "contract-code:S-2026-07-"}
    assert "max(contracts_upstream.contract_code)" in db.calls[1][0]
