"""
API Integration Tests
Tests for complete API workflows and endpoints
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
import io
import zipfile
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.system import SysDictionary
from app.models.contract_upstream import (
    ContractUpstream,
    FinanceUpstreamReceivable,
    FinanceUpstreamInvoice,
    FinanceUpstreamReceipt,
    ProjectSettlement,
)
from app.models.contract_downstream import (
    ContractDownstream,
    FinanceDownstreamPayable,
    FinanceDownstreamInvoice,
    FinanceDownstreamPayment,
    DownstreamSettlement,
)
from app.models.contract_management import (
    ContractManagement,
    FinanceManagementPayable,
    FinanceManagementInvoice,
    FinanceManagementPayment,
    ManagementSettlement,
)
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor
from app.services.report_cache import invalidate_dashboard_cache


async def _seed_upstream_query_graph(test_db: AsyncSession, test_admin: User) -> dict:
    suffix = uuid4().hex[:8].upper()
    contract_name = f"QUERY 上游合同 {suffix}"
    party_a_name = f"聚合甲方 {suffix}"
    excluded_contract_name = f"QUERY 过滤排除合同 {suffix}"
    upstream = ContractUpstream(
        serial_number=9301,
        contract_code=f"QUERY-UP-{suffix}",
        contract_name=contract_name,
        party_a_name=party_a_name,
        party_b_name="聚合乙方",
        company_category="市区配网",
        category="工程类",
        management_mode="自营",
        contract_amount=Decimal("10000.00"),
        sign_date=date(2026, 2, 10),
        status="执行中",
        created_by=test_admin.id,
    )
    downstream = ContractDownstream(
        serial_number=9302,
        contract_code=f"QUERY-DS-{suffix}",
        contract_name="QUERY 下游合同",
        party_a_name="我方公司",
        party_b_name="下游乙方",
        contract_amount=Decimal("3500.00"),
        sign_date=date(2026, 2, 11),
        status="执行中",
        created_by=test_admin.id,
    )
    management = ContractManagement(
        serial_number=9303,
        contract_code=f"QUERY-MGMT-{suffix}",
        contract_name="QUERY 管理合同",
        party_a_name="我方公司",
        party_b_name="管理乙方",
        company_category="项目费用",
        category="服务类",
        contract_amount=Decimal("2200.00"),
        sign_date=date(2026, 2, 12),
        status="执行中",
        created_by=test_admin.id,
    )
    excluded_upstream = ContractUpstream(
        serial_number=9304,
        contract_code=f"QUERY-EX-{suffix}",
        contract_name=excluded_contract_name,
        party_a_name=f"其他甲方 {suffix}",
        party_b_name="其他乙方",
        company_category="用户工程",
        category="工程类",
        contract_amount=Decimal("5000.00"),
        sign_date=date(2026, 2, 13),
        status="执行中",
        created_by=test_admin.id,
    )

    test_db.add_all([upstream, downstream, management, excluded_upstream])
    await test_db.flush()

    downstream.upstream_contract_id = upstream.id
    management.upstream_contract_id = upstream.id

    expense = ExpenseNonContract(
        expense_code="QUERY-EXP-001",
        attribution="PROJECT",
        category="项目费用",
        expense_type="管理费",
        amount=Decimal("88.00"),
        expense_date=date(2026, 2, 24),
        upstream_contract_id=upstream.id,
        description="查询聚合费用",
        created_by=test_admin.id,
        updated_by=test_admin.id,
    )
    expense_second = ExpenseNonContract(
        expense_code="QUERY-EXP-002",
        attribution="PROJECT",
        category="项目费用",
        expense_type="培训费",
        amount=Decimal("32.00"),
        expense_date=date(2026, 2, 26),
        upstream_contract_id=upstream.id,
        description="查询聚合费用-培训",
        created_by=test_admin.id,
        updated_by=test_admin.id,
    )
    zero_hour = ZeroHourLabor(
        labor_date=date(2026, 2, 25),
        attribution="PROJECT",
        upstream_contract_id=upstream.id,
        dispatch_unit="零星用工班组",
        skilled_unit_price=Decimal("0.00"),
        skilled_quantity=Decimal("0.00"),
        skilled_price_total=Decimal("0.00"),
        general_unit_price=Decimal("260.00"),
        general_quantity=Decimal("4.00"),
        general_price_total=Decimal("1040.00"),
        total_amount=Decimal("1040.00"),
        created_by=test_admin.id,
    )
    test_db.add_all([
        expense,
        expense_second,
        zero_hour,
        ProjectSettlement(
            contract_id=upstream.id,
            settlement_date=date(2026, 2, 28),
            completion_date=date(2026, 3, 5),
            warranty_date=date(2027, 3, 5),
            settlement_amount=Decimal("2600.00"),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
        FinanceDownstreamPayable(
            contract_id=downstream.id,
            category="进度款",
            amount=Decimal("1200.00"),
            description="下游应付",
            expected_date=date(2026, 2, 15),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
        FinanceDownstreamPayment(
            contract_id=downstream.id,
            amount=Decimal("800.00"),
            description="下游已付",
            payment_date=date(2026, 2, 20),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
        DownstreamSettlement(
            contract_id=downstream.id,
            settlement_date=date(2026, 2, 21),
            settlement_amount=Decimal("500.00"),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
        FinanceManagementPayable(
            contract_id=management.id,
            category="服务费",
            amount=Decimal("900.00"),
            description="管理应付",
            expected_date=date(2026, 2, 18),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
        FinanceManagementPayment(
            contract_id=management.id,
            amount=Decimal("700.00"),
            description="管理已付",
            payment_date=date(2026, 2, 22),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
        ManagementSettlement(
            contract_id=management.id,
            settlement_date=date(2026, 2, 23),
            settlement_amount=Decimal("300.00"),
            created_by=test_admin.id,
            updated_by=test_admin.id,
        ),
    ])
    seeded = {
        "contract_name": contract_name,
        "party_a_name": party_a_name,
        "excluded_contract_name": excluded_contract_name,
        "expense_total": 120.0,
        "zero_hour_total": 1040.0,
        "downstream_contract_count": 1,
        "downstream_contract_amount": 3500.0,
        "downstream_settlement_amount": 500.0,
        "downstream_paid_amount": 800.0,
        "management_contract_count": 1,
        "management_contract_amount": 2200.0,
        "management_settlement_amount": 300.0,
        "management_paid_amount": 700.0,
        "management_mode": "自营",
        "completion_date": "2026-03-05",
        "warranty_date": "2027-03-05",
    }
    await test_db.commit()

    return seeded


@pytest.fixture
def sample_upstream_contract(event_loop, test_db: AsyncSession, test_admin: User) -> ContractUpstream:
    """Create a sample upstream contract"""
    async def _create():
        contract = ContractUpstream(
            serial_number=100,
            contract_code="API-TEST-001",
            contract_name="API Test Contract",
            party_a_name="Test Party A",
            party_b_name="Test Party B",
            category="工程类",
            contract_amount=Decimal("200000.00"),
            sign_date=date(2024, 6, 1),
            status="执行中",
            created_by=test_admin.id
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)
        return contract

    return event_loop.run_until_complete(_create())


@pytest.mark.asyncio
class TestContractAPIEndpoints:
    """Test contract API endpoints"""
    
    async def test_list_upstream_contracts(
        self,
        client: AsyncClient,
        admin_token: str,
        sample_upstream_contract: ContractUpstream
    ):
        """Test listing upstream contracts"""
        response = await client.get(
            "/api/v1/contracts/upstream/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
    
    async def test_get_upstream_contract(
        self,
        client: AsyncClient,
        admin_token: str,
        sample_upstream_contract: ContractUpstream
    ):
        """Test getting a specific upstream contract"""
        response = await client.get(
            f"/api/v1/contracts/upstream/{sample_upstream_contract.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["contract_code"] == "API-TEST-001"
        assert data["contract_name"] == "API Test Contract"
    
    async def test_get_upstream_contract_not_found(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test getting non-existent contract"""
        response = await client.get(
            "/api/v1/contracts/upstream/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    async def test_unauthorized_access(
        self,
        client: AsyncClient
    ):
        """Test accessing contracts without authentication"""
        response = await client.get("/api/v1/contracts/upstream/")
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestContractSearchEndpoint:
    """Test contract search assistant endpoint"""

    async def test_search_with_sign_date_and_category_filters(
        self,
        client: AsyncClient,
        admin_token: str,
        test_db: AsyncSession,
        test_admin: User
    ):
        """Search should support sign_date range and combine with company_category/query filters."""
        in_range = ContractUpstream(
            serial_number=9101,
            contract_code="SEARCH-DATE-001",
            contract_name="日期筛选命中合同",
            party_a_name="甲方A",
            party_b_name="乙方A",
            company_category="市区配网",
            category="工程类",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2026, 1, 15),
            status="执行中",
            created_by=test_admin.id
        )
        out_of_range = ContractUpstream(
            serial_number=9102,
            contract_code="SEARCH-DATE-002",
            contract_name="日期筛选超范围合同",
            party_a_name="甲方A",
            party_b_name="乙方A",
            company_category="市区配网",
            category="工程类",
            contract_amount=Decimal("2000.00"),
            sign_date=date(2026, 3, 1),
            status="执行中",
            created_by=test_admin.id
        )
        wrong_category = ContractUpstream(
            serial_number=9103,
            contract_code="SEARCH-DATE-003",
            contract_name="日期范围内但分类不匹配",
            party_a_name="甲方A",
            party_b_name="乙方A",
            company_category="用户工程",
            category="工程类",
            contract_amount=Decimal("3000.00"),
            sign_date=date(2026, 1, 20),
            status="执行中",
            created_by=test_admin.id
        )
        test_db.add_all([in_range, out_of_range, wrong_category])
        await test_db.commit()

        response = await client.get(
            "/api/v1/contracts/search",
            params={
                "query": "SEARCH-DATE",
                "company_category": "市区配网",
                "sign_date_start": "2026-01-01",
                "sign_date_end": "2026-01-31",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["contract_code"] == "SEARCH-DATE-001"

    async def test_upstream_query_returns_aggregated_related_metrics(
        self,
        client: AsyncClient,
        admin_token: str,
        test_db: AsyncSession,
        test_admin: User,
    ):
        seeded = await _seed_upstream_query_graph(test_db, test_admin)
        response = await client.get(
            "/api/v1/contracts/search/upstream-query",
            params={"keyword": seeded["contract_name"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        row = payload["items"][0]
        assert row["contract_name"] == seeded["contract_name"]
        assert row["party_a_name"] == seeded["party_a_name"]
        assert row["management_mode"] == seeded["management_mode"]
        assert row["completion_date"] == seeded["completion_date"]
        assert row["warranty_date"] == seeded["warranty_date"]
        assert row["downstream_contract_count"] == seeded["downstream_contract_count"]
        assert row["downstream_contract_amount"] == pytest.approx(seeded["downstream_contract_amount"])
        assert row["downstream_settlement_amount"] == pytest.approx(seeded["downstream_settlement_amount"])
        assert row["downstream_paid_amount"] == pytest.approx(seeded["downstream_paid_amount"])
        assert row["management_contract_count"] == seeded["management_contract_count"]
        assert row["management_contract_amount"] == pytest.approx(seeded["management_contract_amount"])
        assert row["management_settlement_amount"] == pytest.approx(seeded["management_settlement_amount"])
        assert row["management_paid_amount"] == pytest.approx(seeded["management_paid_amount"])
        assert row["non_contract_expense_total"] == pytest.approx(seeded["expense_total"])
        assert row["expenses_by_category"] == [
            {"category": "培训费", "amount": pytest.approx(32.0)},
            {"category": "管理费", "amount": pytest.approx(88.0)},
        ]
        assert row["zero_hour_labor_total"] == pytest.approx(seeded["zero_hour_total"])

    async def test_upstream_query_export_respects_filters(
        self,
        client: AsyncClient,
        admin_token: str,
        test_db: AsyncSession,
        test_admin: User,
    ):
        seeded = await _seed_upstream_query_graph(test_db, test_admin)
        response = await client.get(
            "/api/v1/contracts/search/upstream-query/export",
            params={"party_a_name": seeded["party_a_name"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        workbook = zipfile.ZipFile(io.BytesIO(response.content))
        assert "[Content_Types].xml" in workbook.namelist()
        workbook_text = "\n".join(
            workbook.read(name).decode("utf-8", errors="ignore")
            for name in workbook.namelist()
            if name.endswith(".xml")
        )
        assert seeded["contract_name"] in workbook_text
        assert seeded["excluded_contract_name"] not in workbook_text

@pytest.mark.asyncio
class TestDashboardEndpoints:
    async def test_dashboard_stats_uses_real_summary_data_without_demo_bar_series(
        self,
        client: AsyncClient,
        admin_token: str,
        test_db: AsyncSession,
        test_admin: User,
    ):
        """Dashboard stats should return real summary aggregates and omit the old demo bar payload."""
        current_year = datetime.now().year

        upstream = ContractUpstream(
            serial_number=9501,
            contract_code="DASHBOARD-REAL-001",
            contract_name="经营总览真实聚合合同",
            party_a_name="甲方总览",
            party_b_name="乙方总览",
            category="安装",
            company_category="测试公司分类",
            contract_amount=Decimal("320000.00"),
            sign_date=date(current_year, 3, 12),
            status="执行中",
            created_by=test_admin.id,
        )
        test_db.add(upstream)
        await test_db.commit()

        await invalidate_dashboard_cache(current_year)

        response = await client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cards"]["annual_upstream_count"] == 1
        assert data["cards"]["annual_upstream_amount"] == pytest.approx(320000.0)
        assert data["charts"]["pie_category"] == [{"name": "安装", "value": 320000.0}]
        assert data["charts"]["pie_company"] == [{"name": "测试公司分类", "value": 320000.0}]
        assert "bar" not in data["charts"]

    async def test_search_party_b_with_sign_date_range(
        self,
        client: AsyncClient,
        admin_token: str,
        test_db: AsyncSession,
        test_admin: User
    ):
        """Party B search should support combining with sign_date range."""
        up = ContractUpstream(
            serial_number=9201,
            contract_code="SEARCH-DS-UP-001",
            contract_name="下游筛选上游合同",
            party_a_name="甲方B",
            party_b_name="乙方B",
            category="工程类",
            contract_amount=Decimal("5000.00"),
            sign_date=date(2026, 1, 10),
            status="执行中",
            created_by=test_admin.id
        )
        test_db.add(up)
        await test_db.commit()
        await test_db.refresh(up)

        down_in_range = ContractDownstream(
            serial_number=9301,
            contract_code="SEARCH-DS-001",
            contract_name="下游命中合同",
            party_a_name="示例建设集团",
            party_b_name="供应商日期筛选A",
            upstream_contract_id=up.id,
            contract_amount=Decimal("800.00"),
            sign_date=date(2026, 1, 18),
            status="执行中",
            created_by=test_admin.id
        )
        down_out_of_range = ContractDownstream(
            serial_number=9302,
            contract_code="SEARCH-DS-002",
            contract_name="下游超范围合同",
            party_a_name="示例建设集团",
            party_b_name="供应商日期筛选A",
            upstream_contract_id=up.id,
            contract_amount=Decimal("900.00"),
            sign_date=date(2026, 3, 2),
            status="执行中",
            created_by=test_admin.id
        )
        test_db.add_all([down_in_range, down_out_of_range])
        await test_db.commit()

        response = await client.get(
            "/api/v1/contracts/search",
            params={
                "party_b_name": "供应商日期筛选A",
                "sign_date_start": "2026-01-01",
                "sign_date_end": "2026-01-31",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["downstream_results"]) == 1
        assert data["downstream_results"][0]["contract_code"] == "SEARCH-DS-001"


@pytest.mark.asyncio
class TestReportAPIEndpoints:
    """Test report API endpoints"""
    
    async def test_contracts_summary(
        self,
        client: AsyncClient,
        admin_token: str,
        sample_upstream_contract: ContractUpstream
    ):
        """Test contract summary endpoint"""
        response = await client.get(
            "/api/v1/reports/contracts/summary",
            params={"year": 2024},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "upstream_by_category" in data
        assert "downstream_by_category" in data
    
    async def test_finance_trend(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test finance trend endpoint"""
        response = await client.get(
            "/api/v1/reports/finance/trend",
            params={"year": 2024},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["year"] == 2024
        assert "months" in data
        assert "income" in data
        assert "expense" in data
        assert len(data["months"]) == 12
        assert len(data["income"]) == 12
    
    async def test_ar_ap_stats(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test accounts receivable/payable stats endpoint"""
        response = await client.get(
            "/api/v1/reports/finance/receivables-payables",
            params={"year": 2024},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ar" in data
        assert "ap" in data
        assert "total_receivable" in data["ar"]
        assert "total_payable" in data["ap"]

    async def test_cost_monthly_quarterly_report(
        self,
        client: AsyncClient,
        admin_token: str,
        test_db: AsyncSession,
        test_admin: User
    ):
        """Test monthly/quarterly cost report grouped by upstream company category (business-date based)."""
        apr_ts = datetime(2026, 4, 5, 10, 0, 0)
        # Keep created_at outside Q1 to ensure report uses business dates rather than created_at.
        created_outside_q1 = apr_ts

        # Dictionary rows define display row order/categories.
        test_db.add_all([
            SysDictionary(category="project_category", label="市区配网", value="市区配网", sort_order=1, is_active=True),
            SysDictionary(category="project_category", label="用户工程", value="用户工程", sort_order=2, is_active=True),
        ])

        up_a = ContractUpstream(
            serial_number=201,
            contract_code="UP-COST-001",
            contract_name="上游A",
            party_a_name="甲方A",
            party_b_name="乙方A",
            company_category="市区配网",
            category="工程类",
            contract_amount=Decimal("100.00"),
            sign_date=date(2026, 1, 1),
            status="执行中",
            created_by=test_admin.id,
            created_at=created_outside_q1,
        )
        up_b = ContractUpstream(
            serial_number=202,
            contract_code="UP-COST-002",
            contract_name="上游B",
            party_a_name="甲方B",
            party_b_name="乙方B",
            company_category="用户工程",
            category="工程类",
            contract_amount=Decimal("200.00"),
            sign_date=date(2026, 4, 5),
            status="执行中",
            created_by=test_admin.id,
            created_at=created_outside_q1,
        )
        test_db.add_all([up_a, up_b])
        await test_db.commit()
        await test_db.refresh(up_a)

        down_a = ContractDownstream(
            serial_number=301,
            contract_code="DOWN-COST-001",
            contract_name="下游A",
            party_a_name="示例建设集团",
            party_b_name="供应商A",
            upstream_contract_id=up_a.id,
            contract_amount=Decimal("50.00"),
            sign_date=date(2026, 1, 20),
            status="执行中",
            created_by=test_admin.id,
            created_at=created_outside_q1,
        )
        mgmt_a = ContractManagement(
            serial_number=401,
            contract_code="MGMT-COST-001",
            contract_name="管理A",
            party_a_name="示例建设集团",
            party_b_name="服务商A",
            upstream_contract_id=up_a.id,
            contract_amount=Decimal("60.00"),
            sign_date=date(2026, 1, 25),
            status="执行中",
            created_by=test_admin.id,
            created_at=created_outside_q1,
        )
        test_db.add_all([down_a, mgmt_a])
        await test_db.commit()
        await test_db.refresh(down_a)
        await test_db.refresh(mgmt_a)

        test_db.add_all([
            FinanceUpstreamReceivable(
                contract_id=up_a.id, category="进度款", amount=Decimal("10.00"), expected_date=date(2026, 1, 10), created_at=created_outside_q1
            ),
            FinanceUpstreamInvoice(
                contract_id=up_a.id, invoice_number="INV-UP-1", invoice_date=date(2026, 1, 11), amount=Decimal("20.00"), created_at=created_outside_q1
            ),
            FinanceUpstreamReceipt(
                contract_id=up_a.id, receipt_date=date(2026, 1, 12), amount=Decimal("30.00"), created_at=created_outside_q1
            ),
            ProjectSettlement(
                contract_id=up_a.id, settlement_date=date(2026, 1, 13), settlement_amount=Decimal("40.00"), created_at=created_outside_q1
            ),
            FinanceDownstreamPayable(
                contract_id=down_a.id, category="材料款", amount=Decimal("5.00"), expected_date=date(2026, 1, 14), created_at=created_outside_q1
            ),
            FinanceManagementPayable(
                contract_id=mgmt_a.id, category="服务款", amount=Decimal("6.00"), expected_date=date(2026, 1, 14), created_at=created_outside_q1
            ),
            FinanceDownstreamInvoice(
                contract_id=down_a.id, invoice_number="INV-DOWN-1", invoice_date=date(2026, 1, 15), amount=Decimal("7.00"), created_at=created_outside_q1
            ),
            FinanceManagementInvoice(
                contract_id=mgmt_a.id, invoice_number="INV-MGMT-1", invoice_date=date(2026, 1, 15), amount=Decimal("8.00"), created_at=created_outside_q1
            ),
            FinanceDownstreamPayment(
                contract_id=down_a.id, payment_date=date(2026, 1, 16), amount=Decimal("9.00"), created_at=created_outside_q1
            ),
            FinanceManagementPayment(
                contract_id=mgmt_a.id, payment_date=date(2026, 1, 16), amount=Decimal("10.00"), created_at=created_outside_q1
            ),
            DownstreamSettlement(
                contract_id=down_a.id, settlement_date=date(2026, 1, 17), settlement_amount=Decimal("11.00"), created_at=created_outside_q1
            ),
            ManagementSettlement(
                contract_id=mgmt_a.id, settlement_date=date(2026, 1, 17), settlement_amount=Decimal("12.00"), created_at=created_outside_q1
            ),
            ZeroHourLabor(
                labor_date=date(2026, 1, 18), attribution="PROJECT", upstream_contract_id=up_a.id, total_amount=Decimal("13.00"), created_at=created_outside_q1
            ),
            ExpenseNonContract(
                expense_code="EXP-COST-001",
                attribution="PROJECT",
                category="项目费用",
                expense_type="管理费",
                amount=Decimal("14.00"),
                expense_date=date(2026, 1, 19),
                upstream_contract_id=up_a.id,
                created_by=test_admin.id,
                created_at=created_outside_q1,
            ),
            # Same quarter additions (Q1) to validate quarterly aggregation spans months.
            ExpenseNonContract(
                expense_code="EXP-COST-002",
                attribution="PROJECT",
                category="项目费用",
                expense_type="管理费",
                amount=Decimal("1.00"),
                expense_date=date(2026, 2, 5),
                upstream_contract_id=up_a.id,
                created_by=test_admin.id,
                created_at=created_outside_q1,
            ),
            ZeroHourLabor(
                labor_date=date(2026, 3, 8), attribution="PROJECT", upstream_contract_id=up_a.id, total_amount=Decimal("2.00"), created_at=created_outside_q1
            ),
        ])
        await test_db.commit()

        response = await client.get(
            "/api/v1/reports/cost/monthly-quarterly",
            params={"year": 2026, "month": 1, "skip_cache": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "monthly" in data
        assert "quarterly" in data
        assert "half_yearly" in data
        assert "yearly" in data

        monthly_rows = data["monthly"]["rows"]
        monthly_total = data["monthly"]["total"]
        quarterly_rows = data["quarterly"]["rows"]
        quarterly_total = data["quarterly"]["total"]
        half_yearly_rows = data["half_yearly"]["rows"]
        half_yearly_total = data["half_yearly"]["total"]
        yearly_rows = data["yearly"]["rows"]
        yearly_total = data["yearly"]["total"]

        monthly_city = next(r for r in monthly_rows if r["company_category"] == "市区配网")
        monthly_user = next(r for r in monthly_rows if r["company_category"] == "用户工程")
        quarterly_city = next(r for r in quarterly_rows if r["company_category"] == "市区配网")
        half_yearly_city = next(r for r in half_yearly_rows if r["company_category"] == "市区配网")
        half_yearly_user = next(r for r in half_yearly_rows if r["company_category"] == "用户工程")
        yearly_city = next(r for r in yearly_rows if r["company_category"] == "市区配网")
        yearly_user = next(r for r in yearly_rows if r["company_category"] == "用户工程")

        assert monthly_city["upstream_contract_amount"] == pytest.approx(100.0)
        assert monthly_city["upstream_receivable"] == pytest.approx(10.0)
        assert monthly_city["upstream_invoice"] == pytest.approx(20.0)
        assert monthly_city["upstream_receipt"] == pytest.approx(30.0)
        assert monthly_city["upstream_settlement"] == pytest.approx(40.0)

        assert monthly_city["down_mgmt_contract_amount"] == pytest.approx(110.0)
        assert monthly_city["down_mgmt_payable"] == pytest.approx(11.0)
        assert monthly_city["down_mgmt_invoice"] == pytest.approx(15.0)
        assert monthly_city["down_mgmt_payment"] == pytest.approx(19.0)
        assert monthly_city["down_mgmt_settlement"] == pytest.approx(23.0)

        assert monthly_city["zero_hour_labor"] == pytest.approx(13.0)
        assert monthly_city["non_contract_expense"] == pytest.approx(14.0)
        assert monthly_user["upstream_contract_amount"] == pytest.approx(0.0)
        assert monthly_user["down_mgmt_contract_amount"] == pytest.approx(0.0)

        assert quarterly_city["non_contract_expense"] == pytest.approx(15.0)
        assert quarterly_city["zero_hour_labor"] == pytest.approx(15.0)
        assert quarterly_total["non_contract_expense"] == pytest.approx(15.0)
        assert monthly_total["non_contract_expense"] == pytest.approx(14.0)

        assert half_yearly_city["non_contract_expense"] == pytest.approx(15.0)
        assert half_yearly_city["zero_hour_labor"] == pytest.approx(15.0)
        assert half_yearly_user["upstream_contract_amount"] == pytest.approx(200.0)
        assert half_yearly_total["non_contract_expense"] == pytest.approx(15.0)

        assert yearly_city["non_contract_expense"] == pytest.approx(15.0)
        assert yearly_city["zero_hour_labor"] == pytest.approx(15.0)
        assert yearly_user["upstream_contract_amount"] == pytest.approx(200.0)
        assert yearly_total["non_contract_expense"] == pytest.approx(15.0)

    async def test_export_cost_monthly_quarterly_excel(
        self,
        client: AsyncClient,
        admin_token: str,
    ):
        """Test monthly/quarterly cost report Excel export endpoint"""
        response = await client.get(
            "/api/v1/reports/export/cost/monthly-quarterly",
            params={"year": 2026, "month": 1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        disposition = response.headers.get("content-disposition", "")
        assert "attachment" in disposition
        assert ".xlsx" in disposition

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
            styles_xml = archive.read("xl/styles.xml").decode("utf-8")
        assert "月度成本报表" in workbook_xml
        assert "季度成本报表" in workbook_xml
        assert "半年度成本报表" in workbook_xml
        assert "年度成本报表" in workbook_xml
        # 金额列应启用千分位数字格式
        assert 'formatCode="#,##0.00"' in styles_xml


@pytest.mark.asyncio
class TestCacheInvalidateEndpoint:
    """Test cache invalidation endpoint"""
    
    async def test_admin_can_invalidate_cache(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test that admin can invalidate cache"""
        response = await client.post(
            "/api/v1/reports/cache/invalidate",
            params={"report_type": "contracts_summary", "year": 2024},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invalidated_count" in data
    
    async def test_non_admin_cannot_invalidate_cache(
        self,
        client: AsyncClient,
        user_token: str
    ):
        """Test that regular user cannot invalidate cache"""
        response = await client.post(
            "/api/v1/reports/cache/invalidate",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403


@pytest.mark.asyncio
class TestPagination:
    """Test pagination functionality"""
    
    async def test_pagination_params(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test pagination parameters"""
        response = await client.get(
            "/api/v1/contracts/upstream/",
            params={"page": 1, "page_size": 5},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    async def test_page_size_limit(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test that page size is limited"""
        response = await client.get(
            "/api/v1/contracts/upstream/",
            params={"page": 1, "page_size": 1000},  # Too large
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Different implementations may either cap to max page size or reject invalid input.
        assert response.status_code in (200, 422)
        if response.status_code == 200:
            data = response.json()
            assert data["page_size"] <= 100


@pytest.mark.asyncio
class TestSkipCacheParameter:
    """Test skip_cache parameter for report endpoints"""
    
    async def test_skip_cache_parameter(
        self,
        client: AsyncClient,
        admin_token: str
    ):
        """Test that skip_cache parameter works"""
        # First request - may be cached
        response1 = await client.get(
            "/api/v1/reports/contracts/summary",
            params={"year": 2024, "skip_cache": False},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 200
        
        # Second request with skip_cache - should query database
        response2 = await client.get(
            "/api/v1/reports/contracts/summary",
            params={"year": 2024, "skip_cache": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response2.status_code == 200
