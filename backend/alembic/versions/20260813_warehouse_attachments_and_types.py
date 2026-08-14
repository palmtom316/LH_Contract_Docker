"""Add warehouse document attachments and keep string business types extensible."""

import sqlalchemy as sa
from alembic import op

revision = "20260813_warehouse_attachments_and_types"
down_revision = "20260813_warehouse_consistency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "warehouse_documents",
        sa.Column("delivery_note_file", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("delivery_note_file_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_basis_file", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_basis_file_name", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("warehouse_documents", "scrap_basis_file_name")
    op.drop_column("warehouse_documents", "scrap_basis_file")
    op.drop_column("warehouse_documents", "delivery_note_file_name")
    op.drop_column("warehouse_documents", "delivery_note_file")
