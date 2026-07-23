"""Relax zero-hour finance fields that are optional in the entry workflow."""

from alembic import op
import sqlalchemy as sa


revision = "20260723_zero_hour_finance_fields"
down_revision = "20260722_durable_import_jobs"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    payable_columns = {column["name"]: column for column in inspector.get_columns("finance_zero_hour_payables")}
    invoice_columns = {column["name"]: column for column in inspector.get_columns("finance_zero_hour_invoices")}

    if payable_columns.get("category", {}).get("nullable") is False:
        op.alter_column(
            "finance_zero_hour_payables",
            "category",
            existing_type=sa.String(length=100),
            nullable=True,
        )
    if invoice_columns.get("invoice_number", {}).get("nullable") is False:
        op.alter_column(
            "finance_zero_hour_invoices",
            "invoice_number",
            existing_type=sa.String(length=100),
            nullable=True,
        )


def downgrade():
    # Existing rows may contain NULL values after this release; restoring NOT NULL
    # would be destructive and is intentionally left to an operator-led migration.
    pass
