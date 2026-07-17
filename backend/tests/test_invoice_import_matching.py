from datetime import date
from decimal import Decimal

from app.models.contract_upstream import ContractUpstream
from app.models.invoice_import import InvoiceImportItem
from app.services.invoice_import.matching import InvoiceMatchService, build_dedupe_key, detect_direction
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
        "project_name": "项目名称",
        "construction_project_name": "建筑项目名称",
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


async def test_upstream_matching_prioritizes_construction_project_name(test_db):
    matching_contract = ContractUpstream(
        serial_number=9201,
        contract_code="UP-PROJECT-001",
        contract_name="重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程施工合同",
        party_a_name="国网重庆市电力公司市区供电分公司",
        party_a_tax_no="BUYER-TAX",
        party_b_name="重庆蓝海电力工程有限责任公司",
        contract_amount=Decimal("1000.00"),
    )
    unrelated_contract = ContractUpstream(
        serial_number=9202,
        contract_code="UP-OTHER-001",
        contract_name="其他电力工程施工合同",
        party_a_name="国网重庆市电力公司市区供电分公司",
        party_a_tax_no="BUYER-TAX",
        party_b_name="重庆蓝海电力工程有限责任公司",
        contract_amount=Decimal("1000.00"),
    )
    test_db.add_all([matching_contract, unrelated_contract])
    await test_db.commit()

    item = InvoiceImportItem(
        id=501,
        batch_id=1,
        source_archive_name="invoice.zip",
        direction="upstream",
        buyer_name="国网重庆市电力公司市区供电分公司",
        buyer_tax_no="BUYER-TAX",
        construction_project_name="重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程",
    )
    candidates = await InvoiceMatchService(test_db).find_candidates(item)

    assert len(candidates) == 1
    assert candidates[0].upstream_contract_id == matching_contract.id
    assert candidates[0].matched_signals["construction_project_name"] == 100


async def test_project_name_does_not_fall_back_to_unrelated_same_party_contract(test_db):
    contract = ContractUpstream(
        serial_number=9203,
        contract_code="UP-UNRELATED-001",
        contract_name="完全不同的电力工程施工合同",
        party_a_name="国网重庆市电力公司市区供电分公司",
        party_a_tax_no="BUYER-TAX",
        party_b_name="重庆蓝海电力工程有限责任公司",
        contract_amount=Decimal("1000.00"),
    )
    test_db.add(contract)
    await test_db.commit()

    item = InvoiceImportItem(
        id=502,
        batch_id=1,
        source_archive_name="invoice.zip",
        direction="upstream",
        buyer_name="国网重庆市电力公司市区供电分公司",
        buyer_tax_no="BUYER-TAX",
        construction_project_name="重庆九龙坡110kV劳动村变电站劳港线10kV配套送出工程",
    )

    assert await InvoiceMatchService(test_db).find_candidates(item) == []
