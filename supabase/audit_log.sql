-- ============================================
-- Audit Log System for V1.5
-- ============================================
-- Records all UPDATE and DELETE operations on critical tables
-- for compliance and debugging purposes.
--
-- This implements the pgAudit-like functionality using triggers.

-- ============================================
-- Audit Log Table
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    
    -- What happened
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id INTEGER NOT NULL,
    
    -- When
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Who
    user_id TEXT,  -- From JWT or session
    user_email TEXT,
    ip_address TEXT,
    
    -- What changed
    old_data JSONB,  -- Previous values (for UPDATE/DELETE)
    new_data JSONB,  -- New values (for INSERT/UPDATE)
    changed_fields TEXT[],  -- List of changed column names
    
    -- Context
    request_id TEXT,  -- For request tracing
    user_agent TEXT
);

-- Index for efficient querying
CREATE INDEX IF NOT EXISTS idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record ON audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);

-- ============================================
-- Audit Trigger Function
-- ============================================
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields TEXT[];
    user_id TEXT;
    user_email TEXT;
    key TEXT;
BEGIN
    -- Get user info from JWT claims if available
    BEGIN
        user_id := current_setting('request.jwt.claims', true)::json->>'sub';
        user_email := current_setting('request.jwt.claims', true)::json->>'email';
    EXCEPTION WHEN OTHERS THEN
        user_id := current_user;
        user_email := NULL;
    END;
    
    IF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        new_data := NULL;
        changed_fields := NULL;
        
        INSERT INTO audit_logs (
            table_name, operation, record_id,
            user_id, user_email,
            old_data, new_data, changed_fields
        ) VALUES (
            TG_TABLE_NAME, TG_OP, OLD.id,
            user_id, user_email,
            old_data, new_data, changed_fields
        );
        
        RETURN OLD;
        
    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        
        -- Find changed fields
        changed_fields := ARRAY(
            SELECT key
            FROM jsonb_each(old_data) old_kv
            FULL OUTER JOIN jsonb_each(new_data) new_kv USING (key)
            WHERE old_kv.value IS DISTINCT FROM new_kv.value
        );
        
        -- Only log if something actually changed
        IF array_length(changed_fields, 1) > 0 THEN
            INSERT INTO audit_logs (
                table_name, operation, record_id,
                user_id, user_email,
                old_data, new_data, changed_fields
            ) VALUES (
                TG_TABLE_NAME, TG_OP, NEW.id,
                user_id, user_email,
                old_data, new_data, changed_fields
            );
        END IF;
        
        RETURN NEW;
        
    ELSIF TG_OP = 'INSERT' THEN
        old_data := NULL;
        new_data := to_jsonb(NEW);
        changed_fields := NULL;
        
        INSERT INTO audit_logs (
            table_name, operation, record_id,
            user_id, user_email,
            old_data, new_data, changed_fields
        ) VALUES (
            TG_TABLE_NAME, TG_OP, NEW.id,
            user_id, user_email,
            old_data, new_data, changed_fields
        );
        
        RETURN NEW;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- Apply Triggers to Critical Tables
-- ============================================

-- Upstream Contracts
DROP TRIGGER IF EXISTS audit_contracts_upstream ON contracts_upstream;
CREATE TRIGGER audit_contracts_upstream
    AFTER INSERT OR UPDATE OR DELETE ON contracts_upstream
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Downstream Contracts
DROP TRIGGER IF EXISTS audit_contracts_downstream ON contracts_downstream;
CREATE TRIGGER audit_contracts_downstream
    AFTER INSERT OR UPDATE OR DELETE ON contracts_downstream
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Management Contracts
DROP TRIGGER IF EXISTS audit_contracts_management ON contracts_management;
CREATE TRIGGER audit_contracts_management
    AFTER INSERT OR UPDATE OR DELETE ON contracts_management
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Upstream Finance (critical for money tracking)
DROP TRIGGER IF EXISTS audit_finance_upstream_collections ON finance_upstream_collections;
CREATE TRIGGER audit_finance_upstream_collections
    AFTER INSERT OR UPDATE OR DELETE ON finance_upstream_collections
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Downstream Finance
DROP TRIGGER IF EXISTS audit_finance_downstream_payments ON finance_downstream_payments;
CREATE TRIGGER audit_finance_downstream_payments
    AFTER INSERT OR UPDATE OR DELETE ON finance_downstream_payments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Management Finance
DROP TRIGGER IF EXISTS audit_finance_management_payments ON finance_management_payments;
CREATE TRIGGER audit_finance_management_payments
    AFTER INSERT OR UPDATE OR DELETE ON finance_management_payments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Users table (security critical)
DROP TRIGGER IF EXISTS audit_users ON users;
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============================================
-- Audit Log Query Helpers
-- ============================================

-- View recent audit activity
CREATE OR REPLACE VIEW recent_audit_activity AS
SELECT 
    id,
    timestamp,
    table_name,
    operation,
    record_id,
    user_email,
    changed_fields,
    CASE 
        WHEN operation = 'DELETE' THEN old_data->>'contract_name'
        ELSE new_data->>'contract_name'
    END as contract_name
FROM audit_logs
ORDER BY timestamp DESC
LIMIT 100;

-- Function to get audit history for a specific record
CREATE OR REPLACE FUNCTION get_record_history(
    p_table_name TEXT,
    p_record_id INTEGER
)
RETURNS TABLE (
    timestamp TIMESTAMPTZ,
    operation TEXT,
    user_email TEXT,
    changed_fields TEXT[],
    old_data JSONB,
    new_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.timestamp,
        a.operation,
        a.user_email,
        a.changed_fields,
        a.old_data,
        a.new_data
    FROM audit_logs a
    WHERE a.table_name = p_table_name
    AND a.record_id = p_record_id
    ORDER BY a.timestamp DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON TABLE audit_logs IS 'V1.5: Audit trail for all critical table modifications';
