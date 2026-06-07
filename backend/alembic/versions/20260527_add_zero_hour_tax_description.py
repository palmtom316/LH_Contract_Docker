"""add zero hour tax and description fields

Revision ID: 20260527_add_zero_hour_tax_description
Revises: 20260526_add_downstream_allocations
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260527_add_zero_hour_tax_description'
down_revision = '20260526_add_downstream_allocations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'zero_hour_labor' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('zero_hour_labor')}

    # Add description field
    if 'description' not in existing_columns:
        op.add_column('zero_hour_labor', sa.Column('description', sa.Text(), nullable=True))

    # Add tax_rate field (percentage, max 100.00)
    if 'tax_rate' not in existing_columns:
        op.add_column('zero_hour_labor', sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False))

    # Add tax_amount field
    if 'tax_amount' not in existing_columns:
        op.add_column('zero_hour_labor', sa.Column('tax_amount', sa.Numeric(precision=15, scale=2), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('zero_hour_labor', 'tax_amount')
    op.drop_column('zero_hour_labor', 'tax_rate')
    op.drop_column('zero_hour_labor', 'description')
