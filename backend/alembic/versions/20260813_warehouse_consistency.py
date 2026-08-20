"""Harden warehouse idempotency and reversal uniqueness."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_warehouse_consistency"
down_revision = "20260813_add_warehouse_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    count_columns = {column["name"] for column in inspector.get_columns("warehouse_counts")}
    if "idempotency_key" not in count_columns:
        op.add_column(
            "warehouse_counts",
            sa.Column("idempotency_key", sa.String(length=80), nullable=True),
        )
    count_uniques = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("warehouse_counts")
    }
    if "uq_warehouse_count_idempotency" not in count_uniques:
        op.create_unique_constraint(
            "uq_warehouse_count_idempotency",
            "warehouse_counts",
            ["created_by", "idempotency_key"],
        )
    document_uniques = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("warehouse_documents")
    }
    if "uq_warehouse_document_reversed_document" not in document_uniques:
        op.create_unique_constraint(
            "uq_warehouse_document_reversed_document",
            "warehouse_documents",
            ["reversed_document_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    document_uniques = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("warehouse_documents")
    }
    if "uq_warehouse_document_reversed_document" in document_uniques:
        op.drop_constraint(
            "uq_warehouse_document_reversed_document",
            "warehouse_documents",
            type_="unique",
        )
    count_uniques = {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints("warehouse_counts")
    }
    if "uq_warehouse_count_idempotency" in count_uniques:
        op.drop_constraint(
            "uq_warehouse_count_idempotency",
            "warehouse_counts",
            type_="unique",
        )
    count_columns = {column["name"] for column in sa.inspect(bind).get_columns("warehouse_counts")}
    if "idempotency_key" in count_columns:
        op.drop_column("warehouse_counts", "idempotency_key")
