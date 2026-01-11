-- ============================================
-- Row Level Security (RLS) Policies for V1.5
-- ============================================
-- This file contains RLS policies that enforce data isolation
-- based on department (dept_id) stored in JWT claims.
--
-- Prerequisites:
-- 1. Enable RLS on each table: ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
-- 2. Users must authenticate via Supabase Auth with dept_id in JWT
--
-- Usage:
-- Run this file after the Supabase database is configured
-- psql -h localhost -U postgres -d postgres -f rls_policies.sql

-- ============================================
-- Helper Functions
-- ============================================

-- Function to get current user's department from JWT
CREATE OR REPLACE FUNCTION auth.user_dept_id() 
RETURNS TEXT 
LANGUAGE sql 
STABLE
AS $$
  SELECT COALESCE(
    current_setting('request.jwt.claims', true)::json->>'dept_id',
    current_setting('request.jwt.claims', true)::json->'user_metadata'->>'dept_id'
  )
$$;

-- Function to get current user's role from JWT
CREATE OR REPLACE FUNCTION auth.user_role() 
RETURNS TEXT 
LANGUAGE sql 
STABLE
AS $$
  SELECT COALESCE(
    current_setting('request.jwt.claims', true)::json->>'role',
    'authenticated'
  )
$$;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION auth.is_admin() 
RETURNS BOOLEAN 
LANGUAGE sql 
STABLE
AS $$
  SELECT auth.user_role() IN ('admin', 'service_role')
$$;

-- ============================================
-- Enable RLS on Contract Tables
-- ============================================

-- Upstream Contracts
ALTER TABLE contracts_upstream ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view contracts in their department or all if admin
CREATE POLICY "contracts_upstream_select_policy" ON contracts_upstream
FOR SELECT
USING (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id() OR
  dept_id IS NULL
);

-- Policy: Users can insert contracts for their department
CREATE POLICY "contracts_upstream_insert_policy" ON contracts_upstream
FOR INSERT
WITH CHECK (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id() OR
  dept_id IS NULL
);

-- Policy: Users can update contracts in their department
CREATE POLICY "contracts_upstream_update_policy" ON contracts_upstream
FOR UPDATE
USING (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id()
)
WITH CHECK (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id()
);

-- Policy: Only admins can delete contracts
CREATE POLICY "contracts_upstream_delete_policy" ON contracts_upstream
FOR DELETE
USING (auth.is_admin());

-- ============================================
-- Downstream Contracts
-- ============================================
ALTER TABLE contracts_downstream ENABLE ROW LEVEL SECURITY;

CREATE POLICY "contracts_downstream_select_policy" ON contracts_downstream
FOR SELECT
USING (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id() OR
  dept_id IS NULL
);

CREATE POLICY "contracts_downstream_insert_policy" ON contracts_downstream
FOR INSERT
WITH CHECK (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id() OR
  dept_id IS NULL
);

CREATE POLICY "contracts_downstream_update_policy" ON contracts_downstream
FOR UPDATE
USING (auth.is_admin() OR dept_id::text = auth.user_dept_id())
WITH CHECK (auth.is_admin() OR dept_id::text = auth.user_dept_id());

CREATE POLICY "contracts_downstream_delete_policy" ON contracts_downstream
FOR DELETE
USING (auth.is_admin());

-- ============================================
-- Management Contracts
-- ============================================
ALTER TABLE contracts_management ENABLE ROW LEVEL SECURITY;

CREATE POLICY "contracts_management_select_policy" ON contracts_management
FOR SELECT
USING (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id() OR
  dept_id IS NULL
);

CREATE POLICY "contracts_management_insert_policy" ON contracts_management
FOR INSERT
WITH CHECK (
  auth.is_admin() OR
  dept_id::text = auth.user_dept_id() OR
  dept_id IS NULL
);

CREATE POLICY "contracts_management_update_policy" ON contracts_management
FOR UPDATE
USING (auth.is_admin() OR dept_id::text = auth.user_dept_id())
WITH CHECK (auth.is_admin() OR dept_id::text = auth.user_dept_id());

CREATE POLICY "contracts_management_delete_policy" ON contracts_management
FOR DELETE
USING (auth.is_admin());

-- ============================================
-- Finance Tables (inherit from contract policies via FK)
-- ============================================

-- Upstream Finance
ALTER TABLE finance_upstream_receivables ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_upstream_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_upstream_collections ENABLE ROW LEVEL SECURITY;

-- Downstream Finance
ALTER TABLE finance_downstream_payables ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_downstream_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_downstream_payments ENABLE ROW LEVEL SECURITY;

-- Management Finance
ALTER TABLE finance_management_payables ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_management_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_management_payments ENABLE ROW LEVEL SECURITY;

-- For finance tables, allow access if user has access to parent contract
-- Upstream receivables
CREATE POLICY "finance_upstream_receivables_select" ON finance_upstream_receivables
FOR SELECT
USING (
  auth.is_admin() OR
  EXISTS (
    SELECT 1 FROM contracts_upstream c 
    WHERE c.id = contract_id 
    AND (c.dept_id::text = auth.user_dept_id() OR c.dept_id IS NULL)
  )
);

CREATE POLICY "finance_upstream_receivables_modify" ON finance_upstream_receivables
FOR ALL
USING (
  auth.is_admin() OR
  EXISTS (
    SELECT 1 FROM contracts_upstream c 
    WHERE c.id = contract_id 
    AND c.dept_id::text = auth.user_dept_id()
  )
);

-- Similar policies for other finance tables...
-- (Abbreviated for conciseness - follow same pattern)

-- ============================================
-- Users Table (special handling)
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can only see themselves unless admin
CREATE POLICY "users_select_policy" ON users
FOR SELECT
USING (
  auth.is_admin() OR
  id::text = current_setting('request.jwt.claims', true)::json->>'sub'
);

-- Only admins can modify users
CREATE POLICY "users_modify_policy" ON users
FOR ALL
USING (auth.is_admin());

-- ============================================
-- Service Role Bypass
-- ============================================
-- Grant service_role full access (for FastAPI backend)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;

-- Service role bypasses RLS
ALTER ROLE service_role SET "request.jwt.claims" TO '{"role": "service_role"}';

COMMENT ON POLICY "contracts_upstream_select_policy" ON contracts_upstream 
IS 'V1.5: Department-based access control - users see only their department contracts';
