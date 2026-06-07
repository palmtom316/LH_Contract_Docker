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
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = {
        table: {idx["name"] for idx in inspector.get_indexes(table)}
        for table in [
            "contracts_upstream",
            "contracts_downstream",
            "contracts_management",
        ]
        if table in inspector.get_table_names()
    }

    def create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
        if table_name not in existing_indexes:
            return
        if index_name not in existing_indexes[table_name]:
            op.create_index(index_name, table_name, columns, unique=False)

    # 1. Upstream Contracts
    create_index_if_missing(op.f('ix_contracts_upstream_contract_name'), 'contracts_upstream', ['contract_name'])
    create_index_if_missing(op.f('ix_contracts_upstream_sign_date'), 'contracts_upstream', ['sign_date'])

    # 2. Downstream Contracts
    create_index_if_missing(op.f('ix_contracts_downstream_contract_name'), 'contracts_downstream', ['contract_name'])
    create_index_if_missing(op.f('ix_contracts_downstream_sign_date'), 'contracts_downstream', ['sign_date'])

    # 3. Management Contracts
    create_index_if_missing(op.f('ix_contracts_management_contract_name'), 'contracts_management', ['contract_name'])
    create_index_if_missing(op.f('ix_contracts_management_sign_date'), 'contracts_management', ['sign_date'])


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
