-- Database Index Optimization Script
-- Run this script to add missing indexes for better query performance

-- ============================================
-- Upstream Contracts (上游合同)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_party_a ON contracts_upstream(party_a_name);
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_party_b ON contracts_upstream(party_b_name);
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_status ON contracts_upstream(status);
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_sign_date ON contracts_upstream(sign_date);
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_created_at ON contracts_upstream(created_at);
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_category ON contracts_upstream(category);

-- ============================================
-- Downstream Contracts (下游合同)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_party_a ON contracts_downstream(party_a_name);
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_party_b ON contracts_downstream(party_b_name);
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_status ON contracts_downstream(status);
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_sign_date ON contracts_downstream(sign_date);
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_created_at ON contracts_downstream(created_at);
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_upstream_id ON contracts_downstream(upstream_contract_id);

-- ============================================
-- Management Contracts (管理合同)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_contracts_management_party_a ON contracts_management(party_a_name);
CREATE INDEX IF NOT EXISTS idx_contracts_management_party_b ON contracts_management(party_b_name);
CREATE INDEX IF NOT EXISTS idx_contracts_management_status ON contracts_management(status);
CREATE INDEX IF NOT EXISTS idx_contracts_management_sign_date ON contracts_management(sign_date);
CREATE INDEX IF NOT EXISTS idx_contracts_management_created_at ON contracts_management(created_at);

-- ============================================
-- Finance Tables (财务表)
-- ============================================
-- Upstream Receivables
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receivables_contract ON finance_upstream_receivables(contract_id);
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receivables_date ON finance_upstream_receivables(plan_date);

-- Upstream Invoices
CREATE INDEX IF NOT EXISTS idx_finance_upstream_invoices_contract ON finance_upstream_invoices(contract_id);
CREATE INDEX IF NOT EXISTS idx_finance_upstream_invoices_date ON finance_upstream_invoices(invoice_date);

-- Upstream Receipts
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receipts_contract ON finance_upstream_receipts(contract_id);
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receipts_date ON finance_upstream_receipts(receipt_date);

-- Project Settlements
CREATE INDEX IF NOT EXISTS idx_project_settlements_contract ON project_settlements(contract_id);
CREATE INDEX IF NOT EXISTS idx_project_settlements_date ON project_settlements(settlement_date);

-- ============================================
-- Non-Contract Expenses (无合同费用)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_expenses_non_contract_date ON expenses_non_contract(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_non_contract_category ON expenses_non_contract(category);
CREATE INDEX IF NOT EXISTS idx_expenses_non_contract_attribution ON expenses_non_contract(attribution);

-- ============================================
-- Verification Query
-- ============================================
-- Run this to verify indexes were created:
-- SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename;
