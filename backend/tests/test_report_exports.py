from datetime import date
from decimal import Decimal

from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.routers.reports.exports import (
    _build_association_base_info,
    _build_comprehensive_row,
)


def test_build_comprehensive_row_includes_company_category():
    contract = ContractUpstream(
        id=1,
        serial_number=101,
        contract_code="UP-101",
        contract_name="上游合同一",
        party_a_name="甲方一",
        party_b_name="乙方一",
        company_category="市政工程",
        contract_amount=Decimal("120000.00"),
        sign_date=date(2026, 4, 1),
    )
    contract.receivables = []
    contract.invoices = []
    contract.receipts = [
        FinanceUpstreamReceipt(amount=Decimal("30000.00"), receipt_date=date(2026, 4, 2))
    ]

    row = _build_comprehensive_row(
        contract,
        settlement=None,
        downstream_totals={"settlement": 0, "payable": 0, "paid": 0},
        management_totals={"settlement": 0, "payable": 0, "paid": 0},
        expense_total=0,
        zero_hour_total=0,
    )

    assert row["公司合同分类"] == "市政工程"
    assert row["累计付款金额"] == 30000.0


def test_build_association_base_info_includes_company_category():
    upstream = ContractUpstream(
        id=2,
        serial_number=202,
        contract_code="UP-202",
        contract_name="上游合同二",
        party_a_name="甲方二",
        party_b_name="乙方二",
        company_category="设备采购",
        contract_amount=Decimal("500000.00"),
    )

    base_info = _build_association_base_info(
        upstream,
        up_completion_date=date(2026, 4, 6),
        up_settle_amount=88000.0,
        up_received=66000.0,
    )

    assert base_info["公司合同分类"] == "设备采购"
    assert base_info["上游合同序号"] == 202
