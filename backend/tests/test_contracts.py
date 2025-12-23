"""
Contract Upstream Service Tests
Tests for upstream contract CRUD operations and business logic
"""
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.contract_upstream import ContractUpstream, FinanceUpstreamReceivable
from app.models.user import User, UserRole
from app.services.contract_upstream_service import ContractUpstreamService


@pytest.fixture
async def contract_service(test_db: AsyncSession):
    """Create contract service instance"""
    return ContractUpstreamService(test_db)


@pytest.fixture
async def sample_contract(test_db: AsyncSession, test_user: User) -> ContractUpstream:
    """Create a sample upstream contract for testing"""
    contract = ContractUpstream(
        serial_number=1,
        contract_code="TEST-001",
        contract_name="Test Contract",
        party_a_name="Party A Company",
        party_b_name="Party B Company",
        category="工程类",
        contract_amount=Decimal("100000.00"),
        sign_date=date(2024, 1, 15),
        status="执行中",
        created_by=test_user.id
    )
    test_db.add(contract)
    await test_db.commit()
    await test_db.refresh(contract)
    return contract


@pytest.mark.asyncio
class TestContractUpstreamService:
    """Test ContractUpstreamService methods"""
    
    async def test_get_contract_by_id(
        self, 
        test_db: AsyncSession, 
        sample_contract: ContractUpstream
    ):
        """Test fetching contract by ID"""
        service = ContractUpstreamService(test_db)
        contract = await service.get_contract(sample_contract.id)
        
        assert contract is not None
        assert contract.id == sample_contract.id
        assert contract.contract_code == "TEST-001"
        assert contract.contract_name == "Test Contract"
    
    async def test_get_contract_not_found(self, test_db: AsyncSession):
        """Test fetching non-existent contract"""
        service = ContractUpstreamService(test_db)
        contract = await service.get_contract(99999)
        
        assert contract is None
    
    async def test_list_contracts(
        self, 
        test_db: AsyncSession, 
        sample_contract: ContractUpstream
    ):
        """Test listing contracts with pagination"""
        service = ContractUpstreamService(test_db)
        result = await service.list_contracts(page=1, page_size=10)
        
        assert "items" in result
        assert "total" in result
        assert result["total"] >= 1
        assert len(result["items"]) >= 1
    
    async def test_list_contracts_with_keyword_filter(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test listing contracts with keyword filter"""
        service = ContractUpstreamService(test_db)
        
        # Should find by contract code
        result = await service.list_contracts(keyword="TEST-001")
        assert result["total"] >= 1
        
        # Should not find non-matching keyword
        result = await service.list_contracts(keyword="nonexistent")
        assert result["total"] == 0
    
    async def test_list_contracts_with_status_filter(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test listing contracts with status filter"""
        service = ContractUpstreamService(test_db)
        
        result = await service.list_contracts(status="执行中")
        assert result["total"] >= 1
        
        result = await service.list_contracts(status="已完成")
        # May be 0 if no completed contracts
        assert isinstance(result["total"], int)


@pytest.mark.asyncio
class TestContractFinancialRecords:
    """Test financial record operations for contracts"""
    
    async def test_contract_total_receivable(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test calculating total receivable for a contract"""
        # Add receivable records
        rec1 = FinanceUpstreamReceivable(
            contract_id=sample_contract.id,
            category="进度款",
            amount=Decimal("30000.00"),
            expected_date=date(2024, 2, 1)
        )
        rec2 = FinanceUpstreamReceivable(
            contract_id=sample_contract.id,
            category="验收款",
            amount=Decimal("20000.00"),
            expected_date=date(2024, 3, 1)
        )
        test_db.add_all([rec1, rec2])
        await test_db.commit()
        
        # Refresh contract to get updated relationships
        await test_db.refresh(sample_contract)
        
        # Check total receivable
        assert sample_contract.total_receivable == Decimal("50000.00")
    
    async def test_contract_with_no_receivables(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test contract with no receivable records"""
        await test_db.refresh(sample_contract)
        
        assert sample_contract.total_receivable == 0


@pytest.mark.asyncio
class TestContractValidation:
    """Test contract data validation"""
    
    async def test_unique_contract_code(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test that contract code must be unique"""
        # Try to create another contract with the same code
        duplicate = ContractUpstream(
            contract_code="TEST-001",  # Duplicate!
            contract_name="Another Contract",
            party_a_name="Party A",
            party_b_name="Party B",
            contract_amount=Decimal("50000.00")
        )
        test_db.add(duplicate)
        
        # Should raise an integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            await test_db.commit()
        
        await test_db.rollback()
    
    async def test_unique_serial_number(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test that serial number must be unique"""
        # Try to create another contract with the same serial number
        duplicate = ContractUpstream(
            serial_number=1,  # Duplicate!
            contract_code="TEST-002",
            contract_name="Another Contract",
            party_a_name="Party A",
            party_b_name="Party B",
            contract_amount=Decimal("50000.00")
        )
        test_db.add(duplicate)
        
        # Should raise an integrity error
        with pytest.raises(Exception):
            await test_db.commit()
        
        await test_db.rollback()
