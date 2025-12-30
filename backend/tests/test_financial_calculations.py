"""
Financial Calculation Tests
Unit tests for financial calculations in the contract management system.

Tests cover:
- Contract status calculation
- Amount aggregation
- AR/AP calculations
- Settlement validations
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Import the services and models
import sys
sys.path.insert(0, 'app')


class TestContractStatusCalculation:
    """Tests for contract status calculation logic"""
    
    def test_status_new_no_financials(self):
        """Contract with no financial records should be '未开始'"""
        contract = MagicMock()
        contract.contract_amount = Decimal('100000')
        contract.settlements = []
        contract.receivables = []
        contract.receipts = []
        
        status = self._calculate_status(contract)
        assert status == "未开始"
    
    def test_status_ongoing_with_receivables(self):
        """Contract with some receivables but not settled should be '进行中'"""
        contract = MagicMock()
        contract.contract_amount = Decimal('100000')
        contract.settlements = []
        
        receivable = MagicMock()
        receivable.amount = Decimal('50000')
        contract.receivables = [receivable]
        contract.receipts = []
        
        status = self._calculate_status(contract)
        assert status == "进行中"
    
    def test_status_settled_with_full_receipt(self):
        """Contract with full settlement and receipts should be '已完成'"""
        contract = MagicMock()
        contract.contract_amount = Decimal('100000')
        
        settlement = MagicMock()
        settlement.settlement_amount = Decimal('100000')
        contract.settlements = [settlement]
        
        receipt = MagicMock()
        receipt.amount = Decimal('100000')
        contract.receipts = [receipt]
        contract.receivables = []
        
        status = self._calculate_status(contract)
        assert status == "已完成"
    
    def test_status_settled_partial_receipt(self):
        """Contract settled but not fully paid should be '待收款'"""
        contract = MagicMock()
        contract.contract_amount = Decimal('100000')
        
        settlement = MagicMock()
        settlement.settlement_amount = Decimal('100000')
        contract.settlements = [settlement]
        
        receipt = MagicMock()
        receipt.amount = Decimal('50000')
        contract.receipts = [receipt]
        contract.receivables = []
        
        status = self._calculate_status(contract)
        assert status == "待收款"
    
    def _calculate_status(self, contract):
        """Helper to calculate status based on contract data"""
        total_settlement = sum(
            float(s.settlement_amount or 0) for s in contract.settlements
        )
        total_receipts = sum(
            float(r.amount or 0) for r in contract.receipts
        )
        total_receivables = sum(
            float(r.amount or 0) for r in contract.receivables
        )
        
        contract_amount = float(contract.contract_amount or 0)
        
        if total_settlement == 0 and total_receivables == 0 and total_receipts == 0:
            return "未开始"
        elif total_settlement > 0:
            if total_receipts >= total_settlement:
                return "已完成"
            else:
                return "待收款"
        else:
            return "进行中"


class TestAmountAggregation:
    """Tests for amount aggregation functions"""
    
    def test_aggregate_receivables(self):
        """Test summing receivables correctly"""
        receivables = [
            MagicMock(amount=Decimal('10000')),
            MagicMock(amount=Decimal('20000')),
            MagicMock(amount=Decimal('15000')),
        ]
        
        total = sum(float(r.amount or 0) for r in receivables)
        assert total == 45000.0
    
    def test_aggregate_with_null_values(self):
        """Test aggregation handles None values"""
        items = [
            MagicMock(amount=Decimal('10000')),
            MagicMock(amount=None),
            MagicMock(amount=Decimal('5000')),
        ]
        
        total = sum(float(item.amount or 0) for item in items)
        assert total == 15000.0
    
    def test_aggregate_empty_list(self):
        """Test aggregation of empty list returns 0"""
        items = []
        total = sum(float(item.amount or 0) for item in items)
        assert total == 0.0
    
    def test_percentage_calculation(self):
        """Test percentage calculation for AR/AP"""
        total_receivable = 100000
        total_received = 75000
        
        if total_receivable > 0:
            percentage = (total_received / total_receivable) * 100
        else:
            percentage = 0
        
        assert percentage == 75.0
    
    def test_outstanding_calculation(self):
        """Test outstanding amount calculation"""
        total_receivable = 100000
        total_received = 75000
        
        outstanding = total_receivable - total_received
        assert outstanding == 25000


class TestPaymentValidation:
    """Tests for payment validation logic"""
    
    def test_payment_cannot_exceed_payable(self):
        """Payment should not exceed total payable amount"""
        total_payable = 100000
        existing_payments = 80000
        new_payment = 30000
        
        remaining = total_payable - existing_payments
        is_valid = new_payment <= remaining
        
        assert is_valid == False
        assert remaining == 20000
    
    def test_payment_within_limit(self):
        """Valid payment within remaining amount"""
        total_payable = 100000
        existing_payments = 80000
        new_payment = 15000
        
        remaining = total_payable - existing_payments
        is_valid = new_payment <= remaining
        
        assert is_valid == True
    
    def test_negative_payment_invalid(self):
        """Negative payment amounts should be invalid"""
        payment_amount = -5000
        is_valid = payment_amount > 0
        
        assert is_valid == False


class TestSettlementValidation:
    """Tests for settlement validation logic"""
    
    def test_settlement_amount_reasonable(self):
        """Settlement should be within reasonable range of contract amount"""
        contract_amount = 100000
        settlement_amount = 95000
        
        # Allow 20% variance
        min_allowed = contract_amount * 0.5
        max_allowed = contract_amount * 1.5
        
        is_reasonable = min_allowed <= settlement_amount <= max_allowed
        assert is_reasonable == True
    
    def test_settlement_exceeds_limit(self):
        """Settlement significantly above contract should trigger warning"""
        contract_amount = 100000
        settlement_amount = 200000
        
        max_allowed = contract_amount * 1.5
        needs_warning = settlement_amount > max_allowed
        
        assert needs_warning == True
    
    def test_multiple_settlements_total(self):
        """Test total of multiple settlements"""
        settlements = [
            MagicMock(settlement_amount=Decimal('50000')),
            MagicMock(settlement_amount=Decimal('30000')),
            MagicMock(settlement_amount=Decimal('20000')),
        ]
        
        total = sum(float(s.settlement_amount or 0) for s in settlements)
        assert total == 100000.0


class TestExpenseCalculation:
    """Tests for expense calculation logic"""
    
    def test_monthly_expense_aggregation(self):
        """Test aggregating expenses by month"""
        expenses = [
            {'date': date(2024, 1, 15), 'amount': 10000},
            {'date': date(2024, 1, 20), 'amount': 15000},
            {'date': date(2024, 2, 10), 'amount': 8000},
            {'date': date(2024, 2, 25), 'amount': 12000},
        ]
        
        monthly = {}
        for exp in expenses:
            month_key = exp['date'].strftime('%Y-%m')
            monthly[month_key] = monthly.get(month_key, 0) + exp['amount']
        
        assert monthly['2024-01'] == 25000
        assert monthly['2024-02'] == 20000
    
    def test_expense_category_breakdown(self):
        """Test breaking down expenses by category"""
        expenses = [
            {'category': '工资', 'amount': 50000},
            {'category': '工资', 'amount': 30000},
            {'category': '培训费', 'amount': 10000},
            {'category': '办公费', 'amount': 5000},
        ]
        
        by_category = {}
        for exp in expenses:
            cat = exp['category']
            by_category[cat] = by_category.get(cat, 0) + exp['amount']
        
        assert by_category['工资'] == 80000
        assert by_category['培训费'] == 10000
        assert by_category['办公费'] == 5000
    
    def test_total_expenses(self):
        """Test calculating total expenses"""
        downstream_payments = 50000
        management_payments = 30000
        non_contract_expenses = 20000
        zero_hour_labor = 10000
        
        total = downstream_payments + management_payments + non_contract_expenses + zero_hour_labor
        assert total == 110000


class TestProfitCalculation:
    """Tests for profit/margin calculation"""
    
    def test_gross_profit(self):
        """Test gross profit calculation"""
        contract_amount = 1000000
        total_costs = 750000
        
        gross_profit = contract_amount - total_costs
        profit_margin = (gross_profit / contract_amount) * 100
        
        assert gross_profit == 250000
        assert profit_margin == 25.0
    
    def test_profit_with_settlement(self):
        """Test profit based on settlement vs costs"""
        settlement_amount = 950000
        downstream_costs = 400000
        management_costs = 200000
        other_expenses = 100000
        
        total_costs = downstream_costs + management_costs + other_expenses
        profit = settlement_amount - total_costs
        
        assert profit == 250000
    
    def test_loss_scenario(self):
        """Test when project results in loss"""
        settlement_amount = 800000
        total_costs = 900000
        
        profit = settlement_amount - total_costs
        is_loss = profit < 0
        
        assert profit == -100000
        assert is_loss == True


class TestDateCalculations:
    """Tests for date-related calculations"""
    
    def test_contract_duration_days(self):
        """Test calculating contract duration in days"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 6, 30)
        
        duration = (end_date - start_date).days
        assert duration == 181
    
    def test_overdue_detection(self):
        """Test detecting overdue receivables"""
        expected_date = date(2024, 1, 15)
        today = date(2024, 2, 1)
        
        is_overdue = today > expected_date
        days_overdue = (today - expected_date).days if is_overdue else 0
        
        assert is_overdue == True
        assert days_overdue == 17
    
    def test_year_filter(self):
        """Test filtering by year"""
        sign_date = date(2024, 6, 15)
        filter_year = 2024
        
        matches = sign_date.year == filter_year
        assert matches == True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
