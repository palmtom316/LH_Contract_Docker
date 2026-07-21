"""add tax rate to imported invoices

Revision ID: 20260721_invoice_import_tax_rate
Revises: 20260717_invoice_project_matching
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa


revision = "20260721_invoice_import_tax_rate"
down_revision = "20260717_invoice_project_matching"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    columns = {column["name"] for column in sa.inspect(conn).get_columns("invoice_import_items")}
    if "tax_rate" not in columns:
        op.add_column("invoice_import_items", sa.Column("tax_rate", sa.Numeric(precision=5, scale=2), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    columns = {column["name"] for column in sa.inspect(conn).get_columns("invoice_import_items")}
    if "tax_rate" in columns:
        op.drop_column("invoice_import_items", "tax_rate")
