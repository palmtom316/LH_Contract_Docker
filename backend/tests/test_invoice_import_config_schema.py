from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.invoice_import import AllocationCreate, InvoiceDirection


def test_allocation_create_requires_one_target_contract():
    allocation = AllocationCreate(direction=InvoiceDirection.UPSTREAM, upstream_contract_id=1, amount=Decimal("100.00"))

    assert allocation.direction == InvoiceDirection.UPSTREAM
    assert allocation.upstream_contract_id == 1
    assert allocation.downstream_contract_id is None


def test_invoice_direction_values_are_stable():
    assert InvoiceDirection.UPSTREAM.value == "upstream"
    assert InvoiceDirection.DOWNSTREAM.value == "downstream"
    assert InvoiceDirection.UNKNOWN.value == "unknown"


def test_allocation_create_rejects_unknown_direction():
    with pytest.raises(PydanticValidationError):
        AllocationCreate(direction="unknown", amount="10.00")
