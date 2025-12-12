-- Phase 4 DB Migration Script
BEGIN;

-- 1. Contract Upstream
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS serial_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS ix_contracts_upstream_serial_number ON contracts_upstream (serial_number);
CREATE INDEX IF NOT EXISTS ix_contracts_upstream_party_b_name ON contracts_upstream (party_b_name);

-- Initialize serial_number from current id
UPDATE contracts_upstream SET serial_number = id WHERE serial_number IS NULL;

-- Restore Autoincrement for ID
CREATE SEQUENCE IF NOT EXISTS contracts_upstream_id_seq OWNED BY contracts_upstream.id;
SELECT setval('contracts_upstream_id_seq', coalesce(max(id), 0) + 1, false) FROM contracts_upstream;
ALTER TABLE contracts_upstream ALTER COLUMN id SET DEFAULT nextval('contracts_upstream_id_seq');


-- 2. Contract Downstream
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS serial_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS ix_contracts_downstream_serial_number ON contracts_downstream (serial_number);
CREATE INDEX IF NOT EXISTS ix_contracts_downstream_party_b_name ON contracts_downstream (party_b_name);

-- Initialize serial_number from current id
UPDATE contracts_downstream SET serial_number = id WHERE serial_number IS NULL;

-- Restore Autoincrement for ID
CREATE SEQUENCE IF NOT EXISTS contracts_downstream_id_seq OWNED BY contracts_downstream.id;
SELECT setval('contracts_downstream_id_seq', coalesce(max(id), 0) + 1, false) FROM contracts_downstream;
ALTER TABLE contracts_downstream ALTER COLUMN id SET DEFAULT nextval('contracts_downstream_id_seq');


-- 3. Contract Management
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS serial_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS ix_contracts_management_serial_number ON contracts_management (serial_number);
CREATE INDEX IF NOT EXISTS ix_contracts_management_party_b_name ON contracts_management (party_b_name);

-- Initialize serial_number from current id
UPDATE contracts_management SET serial_number = id WHERE serial_number IS NULL;

-- Restore Autoincrement for ID
CREATE SEQUENCE IF NOT EXISTS contracts_management_id_seq OWNED BY contracts_management.id;
SELECT setval('contracts_management_id_seq', coalesce(max(id), 0) + 1, false) FROM contracts_management;
ALTER TABLE contracts_management ALTER COLUMN id SET DEFAULT nextval('contracts_management_id_seq');


-- 4. Audit Fields for Finance Tables
-- Helper function not needed, just raw commands

-- Upstream Finance
ALTER TABLE finance_upstream_receivables ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_upstream_receivables ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE finance_upstream_invoices ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_upstream_invoices ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE finance_upstream_receipts ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_upstream_receipts ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- Downstream Finance
ALTER TABLE finance_downstream_payables ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_downstream_payables ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE finance_downstream_invoices ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_downstream_invoices ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE finance_downstream_payments ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_downstream_payments ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE downstream_settlements ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE downstream_settlements ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- Management Finance
ALTER TABLE finance_management_payables ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_management_payables ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE finance_management_invoices ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_management_invoices ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE finance_management_payments ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE finance_management_payments ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

ALTER TABLE management_settlements ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE management_settlements ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- Expense
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

COMMIT;
