from datetime import date
from decimal import Decimal

from app.services.invoice_import.matching import build_dedupe_key, detect_direction
from app.services.invoice_import.parser import ParsedInvoice


def _parsed(**overrides):
    data = {
        "invoice_number": "INV-001",
        "invoice_code": None,
        "invoice_date": date(2026, 7, 8),
        "seller_name": "我方公司",
        "seller_tax_no": "OUR-TAX",
        "buyer_name": "客户A",
        "buyer_tax_no": "BUYER-TAX",
        "amount_without_tax": Decimal("100.00"),
        "tax_amount": Decimal("6.00"),
        "total_amount": Decimal("106.00"),
        "invoice_type": "数电票",
        "remarks": "HT-001",
        "payload": {},
    }
    data.update(overrides)
    return ParsedInvoice(**data)


def test_detects_upstream_direction_when_seller_is_company():
    assert detect_direction(_parsed(), "OUR-TAX") == "upstream"


def test_detects_downstream_direction_when_buyer_is_company():
    parsed = _parsed(seller_tax_no="SUPPLIER-TAX", buyer_tax_no="OUR-TAX")
    assert detect_direction(parsed, "OUR-TAX") == "downstream"


def test_build_dedupe_key_is_stable():
    key = build_dedupe_key(_parsed())
    assert key == "INV-001|OUR-TAX|BUYER-TAX|2026-07-08|106.00"
