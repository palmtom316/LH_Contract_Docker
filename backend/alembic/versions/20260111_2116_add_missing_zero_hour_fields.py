"""add_missing_zero_hour_fields

Revision ID: v1_5_zero_hour_fix
Revises: v1_5_zero_hour
Create Date: 2026-01-11 21:16:00.000000

UPDATED 2026-01-13: Fixed to use column existence check to avoid DuplicateColumn error
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'v1_5_zero_hour_fix'
down_revision = 'v1_5_zero_hour'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing approval_pdf_key and approval_pdf_storage to zero_hour_labor
    
    Uses column existence check to avoid DuplicateColumn error if columns already exist.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    table = 'zero_hour_labor'
    if table in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns(table)]
        
        # approval_pdf_key
        if 'approval_pdf_key' not in cols:
            op.add_column(table, sa.Column('approval_pdf_key', sa.String(length=500), nullable=True))
        
        # approval_pdf_storage
        if 'approval_pdf_storage' not in cols:
            op.add_column(table, sa.Column('approval_pdf_storage', sa.String(length=50), server_default='local', nullable=True))
        
        print(f"✓ Updated {table} with approval_pdf columns")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    table = 'zero_hour_labor'
    if table in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns(table)]
        
        if 'approval_pdf_storage' in cols:
            op.drop_column(table, 'approval_pdf_storage')
        if 'approval_pdf_key' in cols:
            op.drop_column(table, 'approval_pdf_key')
