from datetime import date
from decimal import Decimal

from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor, ZeroHourLaborMaterial
from app.routers.reports.exports import (
    _build_association_base_info,
    _build_comprehensive_row,
    _build_expense_payment_row,
    _build_zero_hour_labor_report_row,
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


def test_build_association_base_info_places_sign_date_before_amount():
    upstream = ContractUpstream(
        id=3,
        serial_number=303,
        contract_name="上游合同三",
        company_category="房建工程",
        contract_amount=Decimal("1000.00"),
        sign_date=date(2026, 5, 1),
    )

    base_info = _build_association_base_info(
        upstream,
        up_completion_date=None,
        up_settle_amount=0,
        up_received=0,
    )

    keys = list(base_info.keys())
    assert base_info["签约时间"] == date(2026, 5, 1)
    assert keys.index("签约时间") < keys.index("上游签约金额")


def test_build_expense_payment_row_includes_upstream_company_category_before_date():
    upstream = ContractUpstream(
        id=4,
        contract_name="上游合同四",
        company_category="安装工程",
    )
    expense = ExpenseNonContract(
        expense_code="F-001",
        attribution="项目费用",
        category="项目费用",
        expense_type="交通费",
        amount=Decimal("88.50"),
        expense_date=date(2026, 5, 2),
        handler="张三",
        description="打车",
    )
    expense.upstream_contract = upstream

    row = _build_expense_payment_row(1, expense)

    keys = list(row.keys())
    assert row["公司合同分类"] == "安装工程"
    assert row["关联上游合同"] == "上游合同四"
    assert keys.index("公司合同分类") < keys.index("发生日期")


def test_build_zero_hour_labor_report_row_uses_requested_columns():
    upstream = ContractUpstream(
        id=5,
        contract_name="上游合同五",
        company_category="市政工程",
    )
    labor = ZeroHourLabor(
        labor_date=date(2026, 5, 3),
        attribution="PROJECT",
        labor_price_total=Decimal("100.00"),
        vehicle_price_total=Decimal("20.00"),
        total_amount=Decimal("150.00"),
    )
    labor.upstream_contract = upstream
    labor.materials = [
        ZeroHourLaborMaterial(material_name="砂石", material_price_total=Decimal("30.00"))
    ]

    row = _build_zero_hour_labor_report_row(labor)

    assert list(row.keys()) == [
        "用工时间",
        "归宿",
        "上游合同名称",
        "用工费用",
        "用车费用",
        "材料费用",
        "总计",
    ]
    assert row["归宿"] == "项目用工"
    assert row["上游合同名称"] == "上游合同五"
    assert row["用工费用"] == 100.0
    assert row["用车费用"] == 20.0
    assert row["材料费用"] == 30.0
    assert row["总计"] == 150.0
