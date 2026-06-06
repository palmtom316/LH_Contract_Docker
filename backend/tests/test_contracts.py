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
from app.models.contract_management import ContractManagement
from app.models.contract_downstream import ContractDownstream
from app.models.expense import ExpenseNonContract
from app.models.zero_hour_labor import ZeroHourLabor
from app.models.user import User, UserRole
from app.services.contract_upstream_service import ContractUpstreamService
from app.services.contract_management_service import ContractManagementService
from app.services.contract_downstream_service import ContractDownstreamService
from app.core.errors import AppException


@pytest.fixture
def contract_service(test_db: AsyncSession):
    """Create contract service instance"""
    return ContractUpstreamService(test_db)


@pytest.fixture
def sample_contract(event_loop, test_db: AsyncSession, test_user: User) -> ContractUpstream:
    """Create a sample upstream contract for testing"""
    async def _create():
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

    return event_loop.run_until_complete(_create())


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

    async def test_list_contracts_keyword_uses_business_serial_not_system_id(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Numeric keyword should match user-entered serial_number, not DB id."""
        contract = ContractUpstream(
            serial_number=88,
            contract_code="ALPHA-CODE",
            contract_name="Alpha Contract",
            party_a_name="Alpha Party A",
            party_b_name="Alpha Party B",
            category="工程类",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2024, 1, 1),
            status="执行中",
            created_by=test_user.id
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)

        service = ContractUpstreamService(test_db)

        result_by_id = await service.list_contracts(keyword=str(contract.id))
        assert result_by_id["total"] == 0

        result_by_serial = await service.list_contracts(keyword=str(contract.serial_number))
        assert result_by_serial["total"] == 1
        assert result_by_serial["items"][0].id == contract.id

    async def test_delete_contract_blocks_when_related_records_exist(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        upstream = ContractUpstream(
            serial_number=188,
            contract_code="UP-DEL-188",
            contract_name="禁止删除的上游合同",
            party_a_name="甲方",
            party_b_name="乙方",
            category="工程类",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2024, 1, 1),
            status="执行中",
            created_by=test_user.id
        )
        test_db.add(upstream)
        await test_db.commit()
        await test_db.refresh(upstream)

        test_db.add_all([
            ContractDownstream(
                serial_number=288,
                contract_code="DOWN-188",
                contract_name="关联下游合同",
                party_a_name="示例建设集团",
                party_b_name="供应商A",
                upstream_contract_id=upstream.id,
                contract_amount=Decimal("300.00"),
                sign_date=date(2024, 2, 1),
                status="执行中",
                created_by=test_user.id
            ),
            ContractManagement(
                serial_number=388,
                contract_code="MGMT-188",
                contract_name="关联管理合同",
                party_a_name="示例建设集团",
                party_b_name="供应商B",
                upstream_contract_id=upstream.id,
                contract_amount=Decimal("200.00"),
                sign_date=date(2024, 2, 2),
                status="执行中",
                created_by=test_user.id
            ),
            ExpenseNonContract(
                expense_code="EXP-188",
                category="项目费用",
                expense_type="管理费",
                amount=Decimal("50.00"),
                expense_date=date(2024, 2, 3),
                upstream_contract_id=upstream.id,
                created_by=test_user.id
            ),
            ZeroHourLabor(
                labor_date=date(2024, 2, 4),
                attribution="PROJECT",
                upstream_contract_id=upstream.id,
                total_amount=Decimal("80.00"),
                created_by=test_user.id
            )
        ])
        await test_db.commit()

        service = ContractUpstreamService(test_db)

        with pytest.raises(AppException) as exc_info:
          await service.delete_contract(upstream.id, test_user)

        error = exc_info.value
        assert error.status_code == 409
        assert error.message == "上游合同存在关联数据，无法删除"
        assert error.data["related_records"]["downstream_contracts"][0]["contract_code"] == "DOWN-188"
        assert error.data["related_records"]["management_contracts"][0]["contract_code"] == "MGMT-188"
        assert error.data["related_records"]["non_contract_expenses"][0]["expense_code"] == "EXP-188"
        assert error.data["related_records"]["zero_hour_labors"][0]["labor_date"] == "2024-02-04"


@pytest.mark.asyncio
class TestRelatedContractFilters:
    """Test upstream-contract filtering for related list pages."""

    async def test_management_contracts_can_filter_by_upstream_contract(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        upstream_a = ContractUpstream(
            serial_number=1001,
            contract_code="UP-A",
            contract_name="上游A",
            party_a_name="甲方A",
            party_b_name="乙方A",
            category="工程类",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2024, 1, 1),
            status="执行中",
            created_by=test_user.id
        )
        upstream_b = ContractUpstream(
            serial_number=1002,
            contract_code="UP-B",
            contract_name="上游B",
            party_a_name="甲方B",
            party_b_name="乙方B",
            category="工程类",
            contract_amount=Decimal("2000.00"),
            sign_date=date(2024, 1, 2),
            status="执行中",
            created_by=test_user.id
        )
        test_db.add_all([upstream_a, upstream_b])
        await test_db.commit()
        await test_db.refresh(upstream_a)
        await test_db.refresh(upstream_b)

        management_a = ContractManagement(
            serial_number=2001,
            contract_code="MG-A",
            contract_name="管理合同A",
            party_a_name="示例建设集团",
            party_b_name="供应商A",
            upstream_contract_id=upstream_a.id,
            category="管理费",
            contract_amount=Decimal("300.00"),
            sign_date=date(2024, 2, 1),
            status="执行中",
            created_by=test_user.id
        )
        management_b = ContractManagement(
            serial_number=2002,
            contract_code="MG-B",
            contract_name="管理合同B",
            party_a_name="示例建设集团",
            party_b_name="供应商B",
            upstream_contract_id=upstream_b.id,
            category="管理费",
            contract_amount=Decimal("500.00"),
            sign_date=date(2024, 2, 2),
            status="执行中",
            created_by=test_user.id
        )
        test_db.add_all([management_a, management_b])
        await test_db.commit()

        service = ContractManagementService(test_db)
        result = await service.list_contracts(upstream_contract_id=upstream_a.id)

        assert result["total"] == 1
        assert [item.contract_code for item in result["items"]] == ["MG-A"]

    async def test_downstream_contracts_can_filter_by_upstream_contract(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        upstream_a = ContractUpstream(
            serial_number=1101,
            contract_code="DOWN-UP-A",
            contract_name="下游上游A",
            party_a_name="甲方A",
            party_b_name="乙方A",
            category="工程类",
            contract_amount=Decimal("1000.00"),
            sign_date=date(2024, 3, 1),
            status="执行中",
            created_by=test_user.id
        )
        upstream_b = ContractUpstream(
            serial_number=1102,
            contract_code="DOWN-UP-B",
            contract_name="下游上游B",
            party_a_name="甲方B",
            party_b_name="乙方B",
            category="工程类",
            contract_amount=Decimal("2000.00"),
            sign_date=date(2024, 3, 2),
            status="执行中",
            created_by=test_user.id
        )
        test_db.add_all([upstream_a, upstream_b])
        await test_db.commit()
        await test_db.refresh(upstream_a)
        await test_db.refresh(upstream_b)

        downstream_a = ContractDownstream(
            serial_number=2101,
            contract_code="DS-A",
            contract_name="下游合同A",
            party_a_name="示例建设集团",
            party_b_name="乙方A",
            upstream_contract_id=upstream_a.id,
            category="材料采购",
            contract_amount=Decimal("300.00"),
            sign_date=date(2024, 4, 1),
            status="执行中",
            created_by=test_user.id
        )
        downstream_b = ContractDownstream(
            serial_number=2102,
            contract_code="DS-B",
            contract_name="下游合同B",
            party_a_name="示例建设集团",
            party_b_name="乙方B",
            upstream_contract_id=upstream_b.id,
            category="材料采购",
            contract_amount=Decimal("500.00"),
            sign_date=date(2024, 4, 2),
            status="执行中",
            created_by=test_user.id
        )
        test_db.add_all([downstream_a, downstream_b])
        await test_db.commit()

        service = ContractDownstreamService(test_db)
        result = await service.list_contracts(upstream_contract_id=upstream_a.id)

        assert result["total"] == 1
        assert [item.contract_code for item in result["items"]] == ["DS-A"]


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

        await test_db.refresh(sample_contract, attribute_names=["receivables"])

        # Check total receivable
        assert sample_contract.total_receivable == Decimal("50000.00")
    
    async def test_contract_with_no_receivables(
        self,
        test_db: AsyncSession,
        sample_contract: ContractUpstream
    ):
        """Test contract with no receivable records"""
        await test_db.refresh(sample_contract, attribute_names=["receivables"])

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
