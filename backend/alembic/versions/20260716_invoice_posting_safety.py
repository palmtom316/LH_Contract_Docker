"""enforce invoice posting idempotency

Revision ID: 20260716_invoice_posting_safety
Revises: 20260708_add_invoice_imports
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa


revision = "20260716_invoice_posting_safety"
down_revision = "20260708_add_invoice_imports"
branch_labels = None
depends_on = None


_TARGETS = (
    ("finance_upstream_invoices", "ix_finance_upstream_invoices_source_import_allocation_id"),
    ("finance_downstream_invoices", "ix_finance_downstream_invoices_source_import_allocation_id"),
)


def upgrade() -> None:
    conn = op.get_bind()
    for table_name, index_name in _TARGETS:
        duplicates = conn.execute(sa.text(
            f"""
            SELECT source_import_allocation_id
            FROM {table_name}
            WHERE source_import_allocation_id IS NOT NULL
            GROUP BY source_import_allocation_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )).scalar_one_or_none()
        if duplicates is not None:
            raise RuntimeError(
                f"{table_name} contains duplicate imported allocation {duplicates}; "
                "resolve it before upgrading"
            )

        indexes = {index["name"]: index for index in sa.inspect(conn).get_indexes(table_name)}
        existing = indexes.get(index_name)
        if existing and existing.get("unique"):
            continue
        if existing:
            op.drop_index(index_name, table_name=table_name)
        op.create_index(
            index_name,
            table_name,
            ["source_import_allocation_id"],
            unique=True,
        )


def downgrade() -> None:
    for table_name, index_name in reversed(_TARGETS):
        op.drop_index(index_name, table_name=table_name)
        op.create_index(
            index_name,
            table_name,
            ["source_import_allocation_id"],
            unique=False,
        )
