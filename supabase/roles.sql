-- Supabase Database Roles Initialization
-- This script creates the necessary roles for Supabase services

-- Grant necessary permissions to service roles
ALTER USER postgres WITH SUPERUSER;

-- Create roles if they don't exist
DO $$
BEGIN
    -- Authenticator role (used by PostgREST)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'dev_password_change_me';
    END IF;
    
    -- Anonymous role
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;
    
    -- Authenticated role
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;
    
    -- Service role (full access)
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
    END IF;
    
    -- Supabase admin role
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_admin') THEN
        CREATE ROLE supabase_admin LOGIN PASSWORD 'dev_password_change_me' SUPERUSER;
    END IF;
    
    -- Auth admin role
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_auth_admin') THEN
        CREATE ROLE supabase_auth_admin LOGIN PASSWORD 'dev_password_change_me' NOINHERIT;
    END IF;
    
    -- Storage admin role
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_storage_admin') THEN
        CREATE ROLE supabase_storage_admin LOGIN PASSWORD 'dev_password_change_me' NOINHERIT;
    END IF;
END
$$;

-- Grant role memberships
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;
GRANT supabase_admin TO authenticator;

-- Grant schema access
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO anon, authenticated, service_role;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA public;
