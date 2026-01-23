"""Add optimized indexes for contract search and filtering

Revision ID: 20260122_add_optimized_indexes
Revises: v1_5_complete_fix
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260122_add_optimized_indexes'
down_revision = 'v1_5_complete_fix'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Upstream Contracts
    op.create_index(op.f('ix_contracts_upstream_contract_name'), 'contracts_upstream', ['contract_name'], unique=False)
    op.create_index(op.f('ix_contracts_upstream_sign_date'), 'contracts_upstream', ['sign_date'], unique=False)

    # 2. Downstream Contracts
    op.create_index(op.f('ix_contracts_downstream_contract_name'), 'contracts_downstream', ['contract_name'], unique=False)
    op.create_index(op.f('ix_contracts_downstream_sign_date'), 'contracts_downstream', ['sign_date'], unique=False)

    # 3. Management Contracts
    op.create_index(op.f('ix_contracts_management_contract_name'), 'contracts_management', ['contract_name'], unique=False)
    op.create_index(op.f('ix_contracts_management_sign_date'), 'contracts_management', ['sign_date'], unique=False)


def downgrade() -> None:
    # 1. Upstream Contracts
    op.drop_index(op.f('ix_contracts_upstream_sign_date'), table_name='contracts_upstream')
    op.drop_index(op.f('ix_contracts_upstream_contract_name'), table_name='contracts_upstream')

    # 2. Downstream Contracts
    op.drop_index(op.f('ix_contracts_downstream_sign_date'), table_name='contracts_downstream')
    op.drop_index(op.f('ix_contracts_downstream_contract_name'), table_name='contracts_downstream')

    # 3. Management Contracts
    op.drop_index(op.f('ix_contracts_management_sign_date'), table_name='contracts_management')
    op.drop_index(op.f('ix_contracts_management_contract_name'), table_name='contracts_management')
