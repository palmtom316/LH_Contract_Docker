"""Add Zero Hour Labor MinIO keys

Revision ID: 20260111_1930_add_zero_hour_keys
Revises: 20260111_1855_add_specific_minio_keys
Create Date: 2026-01-11 19:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'v1_5_zero_hour'
down_revision = 'v1_5_minio_keys'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    table = 'zero_hour_labor'
    if table in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns(table)]
        
        # dispatch_file_key
        if 'dispatch_file_key' not in cols:
            op.add_column(table, sa.Column('dispatch_file_key', sa.String(500), nullable=True))
            op.add_column(table, sa.Column('dispatch_file_storage', sa.String(50), server_default='local'))
            
        # approval_pdf_key
        if 'approval_pdf_key' not in cols:
            op.add_column(table, sa.Column('approval_pdf_key', sa.String(500), nullable=True))
            op.add_column(table, sa.Column('approval_pdf_storage', sa.String(50), server_default='local'))

def downgrade() -> None:
    pass
