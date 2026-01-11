"""add_missing_zero_hour_fields

Revision ID: v1_5_zero_hour_fix
Revises: v1_5_zero_hour
Create Date: 2026-01-11 21:16:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'v1_5_zero_hour_fix'
down_revision = 'v1_5_zero_hour'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing approval_pdf_key and approval_pdf_storage to zero_hour_labor
    op.add_column('zero_hour_labor', sa.Column('approval_pdf_key', sa.String(length=500), nullable=True))
    op.add_column('zero_hour_labor', sa.Column('approval_pdf_storage', sa.String(length=50), server_default='local', nullable=True))


def downgrade() -> None:
    op.drop_column('zero_hour_labor', 'approval_pdf_storage')
    op.drop_column('zero_hour_labor', 'approval_pdf_key')
