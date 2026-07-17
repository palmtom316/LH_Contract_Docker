"""add invoice project names for contract matching

Revision ID: 20260717_invoice_project_matching
Revises: 20260716_invoice_posting_safety
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa


revision = "20260717_invoice_project_matching"
down_revision = "20260716_invoice_posting_safety"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {column["name"] for column in inspector.get_columns("invoice_import_items")}
    if "project_name" not in columns:
        op.add_column("invoice_import_items", sa.Column("project_name", sa.String(length=500), nullable=True))
    if "construction_project_name" not in columns:
        op.add_column(
            "invoice_import_items",
            sa.Column("construction_project_name", sa.String(length=500), nullable=True),
        )

    indexes = {index["name"] for index in sa.inspect(conn).get_indexes("invoice_import_items")}
    if "ix_invoice_import_items_construction_project_name" not in indexes:
        op.create_index(
            "ix_invoice_import_items_construction_project_name",
            "invoice_import_items",
            ["construction_project_name"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = {index["name"] for index in inspector.get_indexes("invoice_import_items")}
    if "ix_invoice_import_items_construction_project_name" in indexes:
        op.drop_index("ix_invoice_import_items_construction_project_name", table_name="invoice_import_items")

    columns = {column["name"] for column in sa.inspect(conn).get_columns("invoice_import_items")}
    if "construction_project_name" in columns:
        op.drop_column("invoice_import_items", "construction_project_name")
    if "project_name" in columns:
        op.drop_column("invoice_import_items", "project_name")
