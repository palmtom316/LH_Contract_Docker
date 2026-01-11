"""Add storage_provider and file_key columns for MinIO migration

Revision ID: 20260111_1542_add_minio_storage_fields
Revises: 20260110_1952_8b42d1b51cfe_initial_baseline_empty
Create Date: 2026-01-11 15:42:00

This migration adds two new columns to all tables that have file paths:
- storage_provider: 'local' or 'minio' (default 'local')
- file_key: MinIO object key (nullable, populated after migration)

These columns support the hybrid storage architecture where files can be
stored either locally or in MinIO object storage.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260111_1542_add_minio_storage_fields'
down_revision = '20260110_1952_8b42d1b51cfe_initial_baseline_empty'
branch_labels = None
depends_on = None


# Tables that have file paths and need storage migration columns
TABLES_WITH_FILES = [
    "contracts_upstream",
    "contracts_downstream",
    "contracts_management",
    "finance_upstream_receivables",
    "finance_upstream_invoices",
    "finance_upstream_collections",
    "finance_downstream_payables",
    "finance_downstream_invoices",
    "finance_downstream_payments",
    "finance_management_payables",
    "finance_management_invoices",
    "finance_management_payments",
    "downstream_settlements",
    "management_settlements",
]


def upgrade() -> None:
    """Add storage_provider and file_key columns to all file-containing tables"""
    
    for table_name in TABLES_WITH_FILES:
        # Check if table exists before adding columns
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        
        if table_name not in inspector.get_table_names():
            print(f"Table {table_name} does not exist, skipping...")
            continue
        
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Add storage_provider column if not exists
        if 'storage_provider' not in existing_columns:
            op.add_column(
                table_name,
                sa.Column(
                    'storage_provider',
                    sa.String(20),
                    server_default='local',
                    nullable=False
                )
            )
        
        # Add file_key column if not exists
        if 'file_key' not in existing_columns:
            op.add_column(
                table_name,
                sa.Column(
                    'file_key',
                    sa.String(500),
                    nullable=True
                )
            )
        
        print(f"Added storage columns to {table_name}")


def downgrade() -> None:
    """Remove storage_provider and file_key columns"""
    
    for table_name in TABLES_WITH_FILES:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        
        if table_name not in inspector.get_table_names():
            continue
        
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if 'file_key' in existing_columns:
            op.drop_column(table_name, 'file_key')
        
        if 'storage_provider' in existing_columns:
            op.drop_column(table_name, 'storage_provider')
