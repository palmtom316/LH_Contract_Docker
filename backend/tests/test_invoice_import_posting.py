from decimal import Decimal

import pytest

from app.core.errors import ValidationError
from app.services.invoice_import.posting import validate_allocation_total


def test_rejects_allocation_total_above_invoice_total():
    with pytest.raises(ValidationError):
        validate_allocation_total(Decimal("100.00"), [Decimal("60.00"), Decimal("50.00")])


def test_accepts_allocation_total_equal_invoice_total():
    validate_allocation_total(Decimal("100.00"), [Decimal("60.00"), Decimal("40.00")])
