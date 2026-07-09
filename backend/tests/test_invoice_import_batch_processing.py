from datetime import date
from decimal import Decimal

from app.services.invoice_import.matching import build_dedupe_key
from app.services.invoice_import.parser import ParsedInvoice


def test_import_dedupe_key_for_realistic_invoice():
    parsed = ParsedInvoice(
        invoice_number="24572000000000123456",
        invoice_code=None,
        invoice_date=date(2026, 7, 8),
        seller_name="我方公司",
        seller_tax_no="913000000000000001",
        buyer_name="客户A",
        buyer_tax_no="913000000000000002",
        amount_without_tax=Decimal("1000.00"),
        tax_amount=Decimal("60.00"),
        total_amount=Decimal("1060.00"),
        invoice_type="电子发票",
        remarks="项目合同 HT-2026-001",
        payload={},
    )

    assert build_dedupe_key(parsed) == "24572000000000123456|913000000000000001|913000000000000002|2026-07-08|1060.00"
