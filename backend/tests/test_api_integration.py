"""
API Integration Tests
Tests for complete API workflows and endpoints
"""
import pytest
from datetime import date
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.contract_upstream import ContractUpstream


@pytest.fixture
async def sample_upstream_contract(test_db: AsyncSession, test_admin: User) -> ContractUpstream:
    """Create a sample upstream contract"""
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
        
        assert response.status_code == 200
        data = response.json()
        # Should be capped at max page size (usually 100)
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
