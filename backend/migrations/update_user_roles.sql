-- Migration: Update UserRole enum to new RBAC roles
-- Date: 2024-12-14
-- Description: Migrate from old role enum (ADMIN, MANAGER, OPERATOR, VIEWER) to new business department roles

-- Step 1: Create new enum type
DO $$
BEGIN
    -- Check if new enum type exists
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole_new') THEN
        CREATE TYPE userrole_new AS ENUM (
            'ADMIN',
            'COMPANY_LEADER',
            'CONTRACT_MANAGER',
            'FINANCE',
            'ENGINEERING',
            'AUDIT',
            'BIDDING',
            'GENERAL_AFFAIRS'
        );
    END IF;
END $$;

-- Step 2: Update existing users with role mapping
-- ADMIN -> ADMIN (keep)
-- MANAGER -> CONTRACT_MANAGER
-- OPERATOR -> ENGINEERING  
-- VIEWER -> BIDDING (lowest permission)
UPDATE users SET role = 'ADMIN' WHERE role::text = 'ADMIN';

-- For other roles, we need to handle the type conversion
-- First, alter the column to text temporarily
ALTER TABLE users ALTER COLUMN role TYPE TEXT;

-- Apply mapping
UPDATE users SET role = 'CONTRACT_MANAGER' WHERE role = 'MANAGER';
UPDATE users SET role = 'ENGINEERING' WHERE role = 'OPERATOR';
UPDATE users SET role = 'BIDDING' WHERE role = 'VIEWER';

-- Step 3: Drop old enum and rename new one
DROP TYPE IF EXISTS userrole CASCADE;
ALTER TYPE userrole_new RENAME TO userrole;

-- Step 4: Convert column back to enum
ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole;

-- Step 5: Set default
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'BIDDING'::userrole;

-- Verify migration
SELECT id, username, role FROM users;
