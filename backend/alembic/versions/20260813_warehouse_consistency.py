"""Harden warehouse idempotency and reversal uniqueness."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_warehouse_consistency"
down_revision = "20260813_add_warehouse_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "warehouse_counts",
        sa.Column("idempotency_key", sa.String(length=80), nullable=True),
    )
    op.create_unique_constraint(
        "uq_warehouse_count_idempotency",
        "warehouse_counts",
        ["created_by", "idempotency_key"],
    )
    op.create_unique_constraint(
        "uq_warehouse_document_reversed_document",
        "warehouse_documents",
        ["reversed_document_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_warehouse_document_reversed_document",
        "warehouse_documents",
        type_="unique",
    )
    op.drop_constraint(
        "uq_warehouse_count_idempotency",
        "warehouse_counts",
        type_="unique",
    )
    op.drop_column("warehouse_counts", "idempotency_key")
