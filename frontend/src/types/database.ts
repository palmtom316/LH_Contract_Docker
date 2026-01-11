/**
 * Database Types for LH Contract Management System
 * =================================================
 * Auto-generated TypeScript types from database schema.
 * 
 * Usage:
 * import { Database, Tables, Enums } from '@/types/database';
 * 
 * To regenerate (requires Supabase CLI):
 * npx supabase gen types typescript --local > src/types/database.ts
 */

export type Json =
    | string
    | number
    | boolean
    | null
    | { [key: string]: Json | undefined }
    | Json[];

export interface Database {
    public: {
        Tables: {
            // ============================================
            // Contract Tables
            // ============================================
            contracts_upstream: {
                Row: {
                    id: number;
                    serial_number: number | null;
                    contract_code: string;
                    contract_name: string;
                    party_a_name: string;
                    party_b_name: string;
                    category: string | null;
                    company_category: string | null;
                    pricing_mode: string | null;
                    management_mode: string | null;
                    responsible_person: string | null;
                    contract_handler: string | null;
                    contract_manager: string | null;
                    party_a_contact: string | null;
                    party_a_phone: string | null;
                    party_b_contact: string | null;
                    party_b_phone: string | null;
                    contract_amount: number;
                    sign_date: string | null;
                    start_date: string | null;
                    end_date: string | null;
                    contract_file_path: string | null;
                    status: string;
                    notes: string | null;
                    approval_status: string | null;
                    feishu_instance_code: string | null;
                    approval_pdf_path: string | null;
                    created_at: string;
                    updated_at: string | null;
                    created_by: number | null;
                    dept_id: number | null;
                    // V1.5 Storage fields
                    storage_provider: 'local' | 'minio';
                    file_key: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['contracts_upstream']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<
                    Database['public']['Tables']['contracts_upstream']['Insert']
                >;
            };

            contracts_downstream: {
                Row: {
                    id: number;
                    serial_number: number | null;
                    contract_code: string;
                    contract_name: string;
                    party_a_name: string;
                    party_b_name: string;
                    upstream_contract_id: number | null;
                    category: string | null;
                    company_category: string | null;
                    pricing_mode: string | null;
                    management_mode: string | null;
                    responsible_person: string | null;
                    contract_handler: string | null;
                    contract_manager: string | null;
                    party_a_contact: string | null;
                    party_a_phone: string | null;
                    party_b_contact: string | null;
                    party_b_phone: string | null;
                    contract_amount: number;
                    sign_date: string | null;
                    start_date: string | null;
                    end_date: string | null;
                    contract_file_path: string | null;
                    status: string;
                    notes: string | null;
                    approval_status: string | null;
                    feishu_instance_code: string | null;
                    approval_pdf_path: string | null;
                    created_at: string;
                    updated_at: string | null;
                    created_by: number | null;
                    dept_id: number | null;
                    storage_provider: 'local' | 'minio';
                    file_key: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['contracts_downstream']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<
                    Database['public']['Tables']['contracts_downstream']['Insert']
                >;
            };

            contracts_management: {
                Row: {
                    id: number;
                    serial_number: number | null;
                    contract_code: string;
                    contract_name: string;
                    party_a_name: string;
                    party_b_name: string;
                    upstream_contract_id: number | null;
                    category: string | null;
                    company_category: string | null;
                    pricing_mode: string | null;
                    management_mode: string | null;
                    responsible_person: string | null;
                    contract_handler: string | null;
                    contract_manager: string | null;
                    party_a_contact: string | null;
                    party_a_phone: string | null;
                    party_b_contact: string | null;
                    party_b_phone: string | null;
                    contract_amount: number;
                    sign_date: string | null;
                    start_date: string | null;
                    end_date: string | null;
                    contract_file_path: string | null;
                    status: string;
                    notes: string | null;
                    approval_status: string | null;
                    feishu_instance_code: string | null;
                    approval_pdf_path: string | null;
                    created_at: string;
                    updated_at: string | null;
                    created_by: number | null;
                    dept_id: number | null;
                    storage_provider: 'local' | 'minio';
                    file_key: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['contracts_management']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<
                    Database['public']['Tables']['contracts_management']['Insert']
                >;
            };

            // ============================================
            // Finance Tables
            // ============================================
            finance_upstream_receivables: {
                Row: {
                    id: number;
                    contract_id: number;
                    category: string;
                    amount: number;
                    description: string | null;
                    expected_date: string | null;
                    file_path: string | null;
                    created_at: string;
                    updated_at: string | null;
                    created_by: number | null;
                    storage_provider: 'local' | 'minio';
                    file_key: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['finance_upstream_receivables']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<
                    Database['public']['Tables']['finance_upstream_receivables']['Insert']
                >;
            };

            finance_upstream_invoices: {
                Row: {
                    id: number;
                    contract_id: number;
                    invoice_number: string;
                    invoice_date: string;
                    amount: number;
                    tax_rate: number | null;
                    tax_amount: number | null;
                    invoice_type: string | null;
                    buyer_name: string | null;
                    description: string | null;
                    file_path: string | null;
                    created_at: string;
                    updated_at: string | null;
                    created_by: number | null;
                    storage_provider: 'local' | 'minio';
                    file_key: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['finance_upstream_invoices']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<
                    Database['public']['Tables']['finance_upstream_invoices']['Insert']
                >;
            };

            finance_upstream_collections: {
                Row: {
                    id: number;
                    contract_id: number;
                    collection_date: string;
                    amount: number;
                    payment_method: string | null;
                    payer_name: string | null;
                    payer_account: string | null;
                    payer_bank: string | null;
                    description: string | null;
                    file_path: string | null;
                    created_at: string;
                    updated_at: string | null;
                    created_by: number | null;
                    storage_provider: 'local' | 'minio';
                    file_key: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['finance_upstream_collections']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<
                    Database['public']['Tables']['finance_upstream_collections']['Insert']
                >;
            };

            // ============================================
            // User & Auth
            // ============================================
            users: {
                Row: {
                    id: number;
                    username: string;
                    email: string | null;
                    full_name: string | null;
                    hashed_password: string;
                    role: string;
                    is_active: boolean;
                    dept_id: number | null;
                    created_at: string;
                    updated_at: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['users']['Row'],
                    'id' | 'created_at' | 'updated_at'
                >;
                Update: Partial<Database['public']['Tables']['users']['Insert']>;
            };

            // ============================================
            // Audit Logs (V1.5)
            // ============================================
            audit_logs: {
                Row: {
                    id: number;
                    table_name: string;
                    operation: 'INSERT' | 'UPDATE' | 'DELETE';
                    record_id: number;
                    timestamp: string;
                    user_id: string | null;
                    user_email: string | null;
                    ip_address: string | null;
                    old_data: Json | null;
                    new_data: Json | null;
                    changed_fields: string[] | null;
                    request_id: string | null;
                    user_agent: string | null;
                };
                Insert: Omit<
                    Database['public']['Tables']['audit_logs']['Row'],
                    'id' | 'timestamp'
                >;
                Update: never; // Audit logs should not be updated
            };
        };

        Views: {
            recent_audit_activity: {
                Row: {
                    id: number;
                    timestamp: string;
                    table_name: string;
                    operation: string;
                    record_id: number;
                    user_email: string | null;
                    changed_fields: string[] | null;
                    contract_name: string | null;
                };
            };
        };

        Functions: {
            get_record_history: {
                Args: {
                    p_table_name: string;
                    p_record_id: number;
                };
                Returns: {
                    timestamp: string;
                    operation: string;
                    user_email: string | null;
                    changed_fields: string[] | null;
                    old_data: Json | null;
                    new_data: Json | null;
                }[];
            };
        };

        Enums: {
            contract_status: 'draft' | 'pending' | 'active' | 'completed' | 'terminated';
            approval_status: 'DRAFT' | 'PENDING' | 'APPROVED' | 'REJECTED';
            storage_provider: 'local' | 'minio';
        };
    };
}

// ============================================
// Helper Types
// ============================================

// Extract table row type
export type Tables<T extends keyof Database['public']['Tables']> =
    Database['public']['Tables'][T]['Row'];

// Extract insert type
export type TablesInsert<T extends keyof Database['public']['Tables']> =
    Database['public']['Tables'][T]['Insert'];

// Extract update type
export type TablesUpdate<T extends keyof Database['public']['Tables']> =
    Database['public']['Tables'][T]['Update'];

// Extract enum type
export type Enums<T extends keyof Database['public']['Enums']> =
    Database['public']['Enums'][T];

// ============================================
// Commonly Used Types (aliases for convenience)
// ============================================
export type ContractUpstream = Tables<'contracts_upstream'>;
export type ContractDownstream = Tables<'contracts_downstream'>;
export type ContractManagement = Tables<'contracts_management'>;
export type User = Tables<'users'>;
export type AuditLog = Tables<'audit_logs'>;

// Contract type union
export type Contract = ContractUpstream | ContractDownstream | ContractManagement;

// Storage provider type
export type StorageProvider = Enums<'storage_provider'>;
