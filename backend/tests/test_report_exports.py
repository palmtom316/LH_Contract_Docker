from datetime import date
from decimal import Decimal
import io

import pandas as pd

from app.models.contract_downstream import (
    ContractDownstream,
    DownstreamSettlement,
    FinanceDownstreamPayment,
)
from app.models.contract_management import (
    ContractManagement,
    FinanceManagementPayment,
    ManagementSettlement,
)
from app.models.contract_upstream import (
    ContractUpstream,
    FinanceUpstreamInvoice,
    FinanceUpstreamReceipt,
    ProjectSettlement,
)
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor, ZeroHourLaborMaterial
from app.routers.reports import exports
from app.routers.reports.exports import (
    _build_association_base_info,
    _build_comprehensive_row,
    _build_expense_payment_row,
    _build_upstream_invoice_receipt_comprehensive_row,
    _build_zero_hour_labor_report_row,
)
from app.routers.reports.summary import _build_settlement_report_row


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


def test_build_upstream_invoice_receipt_comprehensive_row_filters_date_range():
    contract = ContractUpstream(
        id=6,
        serial_number=606,
        contract_code="UP-606",
        contract_name="上游合同六",
        party_a_name="甲方六",
        party_b_name="乙方六",
        company_category="市政工程",
        management_mode="自营",
        contract_amount=Decimal("100000.00"),
        sign_date=date(2026, 5, 1),
    )
    contract.invoices = [
        FinanceUpstreamInvoice(invoice_date=date(2026, 4, 30), amount=Decimal("1000.00")),
        FinanceUpstreamInvoice(invoice_date=date(2026, 5, 10), amount=Decimal("2000.00")),
    ]
    contract.receipts = [
        FinanceUpstreamReceipt(receipt_date=date(2026, 5, 15), amount=Decimal("3000.00")),
        FinanceUpstreamReceipt(receipt_date=date(2026, 6, 1), amount=Decimal("4000.00")),
    ]
    contract.settlements = [
        ProjectSettlement(settlement_date=date(2026, 5, 20), settlement_amount=Decimal("90000.00"))
    ]

    row = _build_upstream_invoice_receipt_comprehensive_row(
        contract,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 31),
    )

    assert list(row.keys()) == exports.UPSTREAM_INVOICE_RECEIPT_COMPREHENSIVE_COLUMNS
    assert row["合同序号"] == 606
    assert row["管理模式"] == "自营"
    assert row["合同挂账日期"] == "2026-05-10"
    assert row["合同挂账金额"] == 2000.0
    assert row["合同收款日期"] == "2026-05-15"
    assert row["合同收款金额"] == 3000.0
    assert row["合同结算时间"] == date(2026, 5, 20)
    assert row["合同结算金额"] == 90000.0


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


def test_build_settlement_report_row_uses_requested_columns_and_combines_related_amounts():
    contract = ContractUpstream(
        serial_number=709,
        contract_code="UP-SETTLEMENT-709",
        contract_name="结算合同",
        party_a_name="甲方单位",
        party_b_name="本公司",
        company_category="市政工程",
        contract_amount=Decimal("100000.00"),
    )
    settlement = ProjectSettlement(
        settlement_date=date(2026, 5, 20),
        settlement_amount=Decimal("98000.00"),
    )

    row = _build_settlement_report_row(
        contract,
        settlement,
        received_amount=60000,
        downstream_settlement_amount=45000,
        management_settlement_amount=18000,
        downstream_paid_amount=30000,
        management_paid_amount=12000,
        non_contract_expense_amount=3000,
        zero_hour_labor_amount=2000,
    )

    assert list(row) == [
        "serial_number",
        "contract_name",
        "company_category",
        "party_a_name",
        "contract_amount",
        "settlement_date",
        "settlement_amount",
        "received_amount",
        "down_mgmt_settlement_amount",
        "down_mgmt_paid_amount",
        "non_contract_expense_amount",
        "zero_hour_labor_amount",
    ]
    assert row["down_mgmt_settlement_amount"] == 63000.0
    assert row["down_mgmt_paid_amount"] == 42000.0


async def test_settlement_report_filters_upstream_settlement_date_and_aggregates_related_amounts(
    client,
    test_db,
    admin_token,
):
    settled_contract = ContractUpstream(
        serial_number=707,
        contract_code="UP-SETTLED-707",
        contract_name="本月结算合同",
        party_a_name="甲方单位",
        party_b_name="本公司",
        company_category="市政工程",
        contract_amount=Decimal("100000.00"),
    )
    outside_contract = ContractUpstream(
        serial_number=708,
        contract_code="UP-SETTLED-708",
        contract_name="上月结算合同",
        party_a_name="其他甲方",
        party_b_name="本公司",
        contract_amount=Decimal("200000.00"),
    )
    test_db.add_all([settled_contract, outside_contract])
    await test_db.flush()

    downstream = ContractDownstream(
        contract_code="DS-SETTLED-707",
        contract_name="关联下游合同",
        party_a_name="本公司",
        party_b_name="下游单位",
        upstream_contract_id=settled_contract.id,
        contract_amount=Decimal("50000.00"),
    )
    management = ContractManagement(
        contract_code="MG-SETTLED-707",
        contract_name="关联管理合同",
        party_a_name="本公司",
        party_b_name="管理单位",
        upstream_contract_id=settled_contract.id,
        contract_amount=Decimal("20000.00"),
    )
    test_db.add_all([downstream, management])
    await test_db.flush()
    test_db.add_all([
        ProjectSettlement(
            contract_id=settled_contract.id,
            settlement_date=date(2026, 5, 20),
            settlement_amount=Decimal("98000.00"),
        ),
        ProjectSettlement(
            contract_id=outside_contract.id,
            settlement_date=date(2026, 4, 30),
            settlement_amount=Decimal("190000.00"),
        ),
        FinanceUpstreamReceipt(
            contract_id=settled_contract.id,
            receipt_date=date(2026, 6, 1),
            amount=Decimal("60000.00"),
        ),
        DownstreamSettlement(
            contract_id=downstream.id,
            settlement_date=date(2026, 4, 1),
            settlement_amount=Decimal("45000.00"),
        ),
        ManagementSettlement(
            contract_id=management.id,
            settlement_date=date(2026, 4, 2),
            settlement_amount=Decimal("18000.00"),
        ),
        FinanceDownstreamPayment(
            contract_id=downstream.id,
            payment_date=date(2026, 4, 3),
            amount=Decimal("30000.00"),
        ),
        FinanceManagementPayment(
            contract_id=management.id,
            payment_date=date(2026, 4, 4),
            amount=Decimal("12000.00"),
        ),
        ExpenseNonContract(
            expense_code="EXP-SETTLED-707",
            category="项目费用",
            amount=Decimal("3000.00"),
            expense_date=date(2026, 3, 1),
            upstream_contract_id=settled_contract.id,
        ),
        ZeroHourLabor(
            labor_date=date(2026, 3, 2),
            attribution="PROJECT",
            upstream_contract_id=settled_contract.id,
            total_amount=Decimal("2000.00"),
        ),
    ])
    await test_db.commit()

    response = await client.get(
        "/api/v1/reports/settlement/monthly-quarterly",
        params={"year": 2026, "month": 5, "skip_cache": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    monthly_rows = response.json()["monthly"]["rows"]
    assert len(monthly_rows) == 1
    row = monthly_rows[0]
    assert row["serial_number"] == 707
    assert row["settlement_amount"] == 98000.0
    assert row["received_amount"] == 60000.0
    assert row["down_mgmt_settlement_amount"] == 63000.0
    assert row["down_mgmt_paid_amount"] == 42000.0
    assert row["non_contract_expense_amount"] == 3000.0
    assert row["zero_hour_labor_amount"] == 2000.0


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


async def test_export_upstream_invoice_receipt_comprehensive_filters_by_invoice_or_receipt_date_and_category(
    client,
    test_db,
    admin_token,
):
    invoice_match = ContractUpstream(
        serial_number=701,
        contract_code="UP-INV-MATCH",
        contract_name="挂账命中合同",
        party_a_name="甲方一",
        party_b_name="乙方一",
        company_category="市政工程",
        management_mode="自营",
        contract_amount=Decimal("100000.00"),
        sign_date=date(2026, 5, 1),
    )
    receipt_match = ContractUpstream(
        serial_number=702,
        contract_code="UP-REC-MATCH",
        contract_name="收款命中合同",
        party_a_name="甲方二",
        party_b_name="乙方二",
        company_category="市政工程",
        management_mode="联营",
        contract_amount=Decimal("200000.00"),
        sign_date=date(2026, 5, 2),
    )
    date_miss = ContractUpstream(
        serial_number=703,
        contract_code="UP-DATE-MISS",
        contract_name="日期不命中合同",
        party_a_name="甲方三",
        party_b_name="乙方三",
        company_category="市政工程",
        contract_amount=Decimal("300000.00"),
    )
    category_miss = ContractUpstream(
        serial_number=704,
        contract_code="UP-CATEGORY-MISS",
        contract_name="分类不命中合同",
        party_a_name="甲方四",
        party_b_name="乙方四",
        company_category="房建工程",
        contract_amount=Decimal("400000.00"),
    )
    test_db.add_all([invoice_match, receipt_match, date_miss, category_miss])
    await test_db.flush()
    test_db.add_all([
        FinanceUpstreamInvoice(
            contract_id=invoice_match.id,
            invoice_date=date(2026, 5, 10),
            amount=Decimal("11000.00"),
        ),
        FinanceUpstreamReceipt(
            contract_id=invoice_match.id,
            receipt_date=date(2026, 4, 20),
            amount=Decimal("12000.00"),
        ),
        ProjectSettlement(
            contract_id=invoice_match.id,
            settlement_date=date(2026, 5, 30),
            settlement_amount=Decimal("90000.00"),
        ),
        FinanceUpstreamReceipt(
            contract_id=receipt_match.id,
            receipt_date=date(2026, 5, 12),
            amount=Decimal("21000.00"),
        ),
        FinanceUpstreamInvoice(
            contract_id=date_miss.id,
            invoice_date=date(2026, 4, 10),
            amount=Decimal("31000.00"),
        ),
        FinanceUpstreamReceipt(
            contract_id=date_miss.id,
            receipt_date=date(2026, 6, 10),
            amount=Decimal("32000.00"),
        ),
        FinanceUpstreamInvoice(
            contract_id=category_miss.id,
            invoice_date=date(2026, 5, 15),
            amount=Decimal("41000.00"),
        ),
    ])
    await test_db.commit()

    response = await client.get(
        "/api/v1/reports/export/upstream-invoice-receipt-comprehensive",
        params={
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "company_category": "市政工程",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    df = pd.read_excel(io.BytesIO(response.content))
    assert list(df.columns) == exports.UPSTREAM_INVOICE_RECEIPT_COMPREHENSIVE_COLUMNS
    assert set(df["合同名称"]) == {"挂账命中合同", "收款命中合同"}

    rows = {row["合同名称"]: row for _, row in df.iterrows()}
    assert rows["挂账命中合同"]["合同挂账日期"] == "2026-05-10"
    assert rows["挂账命中合同"]["合同挂账金额"] == 11000
    assert rows["挂账命中合同"]["合同收款金额"] == 0
    assert pd.to_datetime(rows["挂账命中合同"]["合同结算时间"]).date() == date(2026, 5, 30)
    assert rows["收款命中合同"]["合同收款日期"] == "2026-05-12"
    assert rows["收款命中合同"]["合同收款金额"] == 21000
    assert rows["收款命中合同"]["合同挂账金额"] == 0
