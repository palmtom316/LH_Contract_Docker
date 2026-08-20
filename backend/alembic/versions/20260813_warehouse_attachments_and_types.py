"""Add warehouse document attachments and keep string business types extensible."""

import sqlalchemy as sa
from alembic import op

revision = "20260813_warehouse_attachments_and_types"
down_revision = "20260813_warehouse_consistency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("warehouse_documents")
    }
    columns = (
        sa.Column("delivery_note_file", sa.String(length=500), nullable=True),
        sa.Column("delivery_note_file_name", sa.String(length=255), nullable=True),
        sa.Column("scrap_basis_file", sa.String(length=500), nullable=True),
        sa.Column("scrap_basis_file_name", sa.String(length=255), nullable=True),
    )
    for column in columns:
        if column.name not in existing:
            op.add_column("warehouse_documents", column)


def downgrade() -> None:
    existing = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("warehouse_documents")
    }
    for name in (
        "scrap_basis_file_name",
        "scrap_basis_file",
        "delivery_note_file_name",
        "delivery_note_file",
    ):
        if name in existing:
            op.drop_column("warehouse_documents", name)
