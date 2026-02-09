"""
API Integration Tests
Tests for complete API workflows and endpoints
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
import io
import zipfile
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
            party_a_name="蓝海",
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
            party_a_name="蓝海",
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
        assert "月度成本报表" in workbook_xml
        assert "季度成本报表" in workbook_xml
        assert "半年度成本报表" in workbook_xml
        assert "年度成本报表" in workbook_xml


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
