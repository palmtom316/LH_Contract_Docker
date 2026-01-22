import { Database } from './database';

type DbContractUpstream = Database['public']['Tables']['contracts_upstream']['Row'];
type DbContractDownstream = Database['public']['Tables']['contracts_downstream']['Row'];
type DbContractManagement = Database['public']['Tables']['contracts_management']['Row'];

// Common fields found in all contract types from API
export interface BaseContractItem {
    id: number;
    contract_code: string;
    contract_name: string;
    contract_amount: number;
    sign_date: string | null;
    status: string;
    created_at: string;

    // Computed/API fields
    total_receivable?: number;
    total_invoiced?: number;
    total_received?: number;
    total_settlement?: number;

    // Downstream specific
    total_payable?: number;
    total_paid?: number;
}

// Specific API responses (merging DB row with API fields)
export interface ContractUpstreamItem extends DbContractUpstream {
    total_receivable: number;
    total_invoiced: number;
    total_received: number;
    total_settlement: number;
}

export interface ContractDownstreamItem extends DbContractDownstream {
    total_payable: number;
    total_invoiced: number;
    total_paid: number;
    total_settlement: number;
    // Fallbacks for compatibility if API differs slightly
    party_a?: string;
    party_b?: string;
}

export interface ContractManagementItem extends DbContractManagement {
    total_payable: number;
    total_invoiced: number;
    total_paid: number;
    total_settlement: number;
}

export type ContractItem = ContractUpstreamItem | ContractDownstreamItem | ContractManagementItem;

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}
