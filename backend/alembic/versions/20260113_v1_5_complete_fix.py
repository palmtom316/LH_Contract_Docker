"""V1.5 Complete Schema Fix - Add all missing columns

Revision ID: v1_5_complete_fix
Revises: v1_5_zero_hour_fix
Create Date: 2026-01-13

This migration ensures ALL V1.5 required columns exist in the database.
It uses IF NOT EXISTS logic via column detection to avoid errors on
databases that already have some columns from previous partial migrations.

Based on 2026-01-13 production upgrade lessons learned.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'v1_5_complete_fix'
down_revision = 'v1_5_zero_hour_fix'
branch_labels = None
depends_on = None


def add_column_if_not_exists(inspector, table_name, column_name, column_type, **kwargs):
    """Helper function to add column only if it doesn't exist"""
    if table_name not in inspector.get_table_names():
        print(f"  Table {table_name} does not exist, skipping")
        return False
    
    cols = [c['name'] for c in inspector.get_columns(table_name)]
    if column_name not in cols:
        op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
        print(f"  ✓ Added {table_name}.{column_name}")
        return True
    else:
        print(f"  - {table_name}.{column_name} already exists")
        return False


def upgrade() -> None:
    """Add all V1.5 required columns with existence checks"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    print("\n=== V1.5 Complete Schema Fix ===\n")
    
    # 1. Contract Tables
    print("1. Updating contract tables...")
    for table in ['contracts_upstream', 'contracts_downstream', 'contracts_management']:
        add_column_if_not_exists(inspector, table, 'contract_file_key', sa.String(500), nullable=True)
        add_column_if_not_exists(inspector, table, 'contract_file_storage', sa.String(50), server_default='local')
        add_column_if_not_exists(inspector, table, 'approval_pdf_key', sa.String(500), nullable=True)
        add_column_if_not_exists(inspector, table, 'approval_pdf_storage', sa.String(50), server_default='local')
    
    # 2. Finance Invoice Tables
    print("\n2. Updating finance invoice tables...")
    for table in ['finance_upstream_invoices', 'finance_downstream_invoices', 'finance_management_invoices']:
        add_column_if_not_exists(inspector, table, 'file_key', sa.String(500), nullable=True)
        add_column_if_not_exists(inspector, table, 'storage_provider', sa.String(50), server_default='local')
    
    # 3. Finance Receivables/Payables/Payments Tables
    print("\n3. Updating finance receivables/payables/payments tables...")
    finance_tables = [
        'finance_upstream_receivables',
        'finance_upstream_receipts',
        'finance_downstream_payables',
        'finance_downstream_payments',
        'finance_management_payables',
        'finance_management_payments'
    ]
    for table in finance_tables:
        add_column_if_not_exists(inspector, table, 'file_key', sa.String(500), nullable=True)
        add_column_if_not_exists(inspector, table, 'storage_provider', sa.String(50), server_default='local')
    
    # 4. Settlement Tables
    print("\n4. Updating settlement tables...")
    for table in ['downstream_settlements', 'management_settlements']:
        add_column_if_not_exists(inspector, table, 'file_key', sa.String(500), nullable=True)
        add_column_if_not_exists(inspector, table, 'storage_provider', sa.String(50), server_default='local')
    
    # 5. Project Settlements (special - has many report columns)
    print("\n5. Updating project_settlements table...")
    table = 'project_settlements'
    add_column_if_not_exists(inspector, table, 'file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'storage_provider', sa.String(50), server_default='local')
    
    # Report-specific columns
    reports = ['audit_report', 'settlement_report', 'start_report', 'completion_report', 
               'visa_records', 'measurement_records', 'progress_payment']
    for report in reports:
        add_column_if_not_exists(inspector, table, f'{report}_key', sa.String(500), nullable=True)
        add_column_if_not_exists(inspector, table, f'{report}_storage', sa.String(50), server_default='local')
    
    # 6. Expenses Non-Contract
    print("\n6. Updating expenses_non_contract table...")
    table = 'expenses_non_contract'
    add_column_if_not_exists(inspector, table, 'file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'storage_provider', sa.String(50), server_default='local')
    add_column_if_not_exists(inspector, table, 'invoice_file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'invoice_file_storage', sa.String(50), server_default='local')
    add_column_if_not_exists(inspector, table, 'approval_pdf_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'approval_pdf_storage', sa.String(50), server_default='local')
    
    # 7. Zero Hour Labor
    print("\n7. Updating zero_hour_labor table...")
    table = 'zero_hour_labor'
    add_column_if_not_exists(inspector, table, 'approval_pdf_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'approval_pdf_storage', sa.String(50), server_default='local')
    add_column_if_not_exists(inspector, table, 'dispatch_file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'dispatch_file_storage', sa.String(50), server_default='local')
    add_column_if_not_exists(inspector, table, 'settlement_file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'settlement_file_storage', sa.String(50), server_default='local')
    add_column_if_not_exists(inspector, table, 'invoice_file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'invoice_file_storage', sa.String(50), server_default='local')
    
    # 8. Zero Hour Labor Materials
    print("\n8. Updating zero_hour_labor_materials table...")
    table = 'zero_hour_labor_materials'
    add_column_if_not_exists(inspector, table, 'file_key', sa.String(500), nullable=True)
    add_column_if_not_exists(inspector, table, 'storage_provider', sa.String(50), server_default='local')
    
    print("\n=== V1.5 Schema Fix Complete ===\n")


def downgrade() -> None:
    """Downgrade is intentionally empty as this is a fix migration.
    
    Dropping columns added by this migration would potentially lose data.
    If rollback is needed, use VM snapshot or database backup instead.
    """
    print("Downgrade for v1_5_complete_fix is not implemented. Use VM snapshot for rollback.")
    pass
