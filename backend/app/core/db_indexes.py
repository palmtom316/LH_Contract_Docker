"""
Database Performance Optimization - Covering Indexes
Creates optimized indexes for common query patterns.

Run this script manually on your PostgreSQL database to improve query performance.

Covering indexes include all columns needed for a query,
allowing the database to return results directly from the index
without accessing the table data (index-only scan).
"""

SQL_SCRIPT = '''
-- =====================================================
-- Performance Optimization Indexes
-- Run this script manually on your PostgreSQL database
-- =====================================================

-- 1. Upstream Contracts - Common List Query
-- Covers: filtering by sign_date year, status; ordering by sign_date
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contracts_upstream_list_query
ON contracts_upstream (sign_date DESC, status)
INCLUDE (id, contract_code, contract_name, party_a_name, contract_amount, category);

-- 2. Upstream Contracts - Filter by Category
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contracts_upstream_category
ON contracts_upstream (category, sign_date DESC)
INCLUDE (id, contract_code, contract_name, contract_amount);

-- 3. Downstream Contracts - Link to Upstream
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contracts_downstream_upstream
ON contracts_downstream (upstream_contract_id, sign_date DESC)
INCLUDE (id, contract_code, contract_name, contract_amount);

-- 4. Downstream Contracts - List Query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contracts_downstream_list
ON contracts_downstream (sign_date DESC, status)
INCLUDE (id, contract_code, contract_name, party_b_name, contract_amount);

-- 5. Management Contracts - List Query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contracts_management_list
ON contracts_management (sign_date DESC, status)
INCLUDE (id, contract_code, contract_name, contract_amount);

-- 6. Upstream Receivables - By Contract
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_upstream_receivables_contract
ON finance_upstream_receivable (contract_id, expected_date)
INCLUDE (amount, description);

-- 7. Upstream Receipts - By Contract and Date
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_upstream_receipts_contract
ON finance_upstream_receipt (contract_id, receipt_date DESC)
INCLUDE (amount);

-- 8. Downstream Payables - By Contract
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_downstream_payables_contract
ON finance_downstream_payable (contract_id, expected_date)
INCLUDE (amount);

-- 9. Downstream Payments - By Contract and Date
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_downstream_payments_contract
ON finance_downstream_payment (contract_id, payment_date DESC)
INCLUDE (amount);

-- 10. Expenses - By Date and Type
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expenses_date_type
ON expenses_non_contract (expense_date DESC, expense_type)
INCLUDE (amount, description, upstream_contract_id);

-- 11. Expenses - By Upstream Contract
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expenses_upstream
ON expenses_non_contract (upstream_contract_id)
WHERE upstream_contract_id IS NOT NULL;

-- 12. Zero Hour Labor - By Date
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zero_hour_labor_date
ON zero_hour_labor (labor_date DESC)
INCLUDE (total_amount, description, upstream_contract_id);

-- 13. Audit Logs - By Date (for cleanup queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_date
ON audit_logs (created_at DESC)
INCLUDE (action, resource_type, user_id);

-- 14. Audit Logs - By User
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user
ON audit_logs (user_id, created_at DESC)
INCLUDE (action, resource_type);

-- 15. Users - Active Users Lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active
ON users (is_active, role)
WHERE is_active = true;

-- 16. Project Settlements - By Contract
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_settlements_contract
ON project_settlement (contract_id)
INCLUDE (settlement_amount, settlement_date, completion_date);


-- =====================================================
-- Partial Indexes for Common Filters
-- =====================================================

-- Active upstream contracts only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_upstream_active
ON contracts_upstream (sign_date DESC)
WHERE status NOT IN ('已取消', '已完成');

-- Pending payments (downstream)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_downstream_pending
ON contracts_downstream (sign_date DESC)
WHERE status IN ('进行中', '待付款');


-- =====================================================
-- Statistics Update
-- =====================================================

-- Update statistics for query planner
ANALYZE contracts_upstream;
ANALYZE contracts_downstream;
ANALYZE contracts_management;
ANALYZE finance_upstream_receivable;
ANALYZE finance_upstream_receipt;
ANALYZE finance_downstream_payable;
ANALYZE finance_downstream_payment;
ANALYZE expenses_non_contract;
ANALYZE zero_hour_labor;
ANALYZE audit_logs;
'''


async def apply_performance_indexes(db):
    """
    Apply performance indexes to the database.
    
    This should be run during maintenance windows as CONCURRENTLY
    indexes require some time but don't block writes.
    """
    import logging
    from sqlalchemy import text
    
    logger = logging.getLogger(__name__)
    
    # Split into individual statements
    statements = [s.strip() for s in SQL_SCRIPT.split(';') if s.strip() and not s.strip().startswith('--')]
    
    success_count = 0
    error_count = 0
    
    for stmt in statements:
        if not stmt:
            continue
        try:
            await db.execute(text(stmt))
            success_count += 1
            logger.info(f"Executed: {stmt[:60]}...")
        except Exception as e:
            error_count += 1
            logger.warning(f"Failed: {stmt[:60]}... Error: {e}")
    
    await db.commit()
    
    return {
        "success_count": success_count,
        "error_count": error_count,
        "message": f"Applied {success_count} index operations, {error_count} errors"
    }


def get_index_sql():
    """Return the raw SQL script for manual execution."""
    return SQL_SCRIPT
