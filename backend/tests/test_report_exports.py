from datetime import date
from decimal import Decimal
import io

import pandas as pd

from app.models.contract_downstream import ContractDownstream, FinanceDownstreamPayment
from app.models.contract_management import ContractManagement, FinanceManagementPayment
from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceipt
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor, ZeroHourLaborMaterial
from app.routers.reports import exports
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


def test_downstream_payment_rows_include_company_category_before_payment_date():
    downstream_contract = ContractDownstream(
        id=10,
        contract_code="DS-001",
        contract_name="下游合同一",
        party_a_name="甲方",
        party_b_name="乙方",
        company_category="市政工程",
        contract_amount=Decimal("1000.00"),
    )
    downstream_payment = FinanceDownstreamPayment(
        payment_date=date(2026, 5, 10),
        amount=Decimal("300.00"),
        payment_method="银行转账",
        payee_name="乙方",
    )
    management_contract = ContractManagement(
        id=11,
        contract_code="MG-001",
        contract_name="管理合同一",
        party_a_name="甲方",
        party_b_name="管理方",
        company_category="房建工程",
        contract_amount=Decimal("2000.00"),
    )
    management_payment = FinanceManagementPayment(
        payment_date=date(2026, 5, 11),
        amount=Decimal("500.00"),
        payment_method="现金",
    )

    downstream_row = exports._build_downstream_payment_row(1, downstream_payment, downstream_contract)
    management_row = exports._build_management_payment_row(2, management_payment, management_contract)

    assert downstream_row["公司合同分类"] == "市政工程"
    assert management_row["公司合同分类"] == "房建工程"
    assert list(downstream_row).index("公司合同分类") < list(downstream_row).index("付款日期")
    assert list(management_row).index("公司合同分类") < list(management_row).index("付款日期")


async def test_export_downstream_payments_filters_by_company_category(
    client,
    test_db,
    admin_token,
):
    matching_downstream = ContractDownstream(
        contract_code="DS-MATCH",
        contract_name="匹配下游合同",
        party_a_name="甲方",
        party_b_name="乙方一",
        company_category="市政工程",
        contract_amount=Decimal("1000.00"),
    )
    other_downstream = ContractDownstream(
        contract_code="DS-OTHER",
        contract_name="其他下游合同",
        party_a_name="甲方",
        party_b_name="乙方二",
        company_category="房建工程",
        contract_amount=Decimal("1000.00"),
    )
    matching_management = ContractManagement(
        contract_code="MG-MATCH",
        contract_name="匹配管理合同",
        party_a_name="甲方",
        party_b_name="管理方",
        company_category="市政工程",
        contract_amount=Decimal("1000.00"),
    )
    test_db.add_all([matching_downstream, other_downstream, matching_management])
    await test_db.flush()
    test_db.add_all([
        FinanceDownstreamPayment(
            contract_id=matching_downstream.id,
            payment_date=date(2026, 5, 10),
            amount=Decimal("100.00"),
        ),
        FinanceDownstreamPayment(
            contract_id=other_downstream.id,
            payment_date=date(2026, 5, 11),
            amount=Decimal("200.00"),
        ),
        FinanceManagementPayment(
            contract_id=matching_management.id,
            payment_date=date(2026, 5, 12),
            amount=Decimal("300.00"),
        ),
    ])
    await test_db.commit()

    response = await client.get(
        "/api/v1/reports/export/payments/downstream",
        params={"company_category": "市政工程"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    df = pd.read_excel(io.BytesIO(response.content))
    assert "公司合同分类" in df.columns
    assert set(df["合同编号"]) == {"DS-MATCH", "MG-MATCH"}
    assert set(df["公司合同分类"]) == {"市政工程"}
