"""add invoice import tables

Revision ID: 20260708_add_invoice_imports
Revises: 20260527_add_zero_hour_tax_description
Create Date: 2026-07-08 09:39:46
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260708_add_invoice_imports"
down_revision = "20260527_add_zero_hour_tax_description"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())
    invoice_tables = {
        "invoice_import_batches",
        "invoice_import_items",
        "invoice_import_allocations",
        "invoice_import_match_candidates",
    }
    if invoice_tables.issubset(existing_tables):
        return

    op.add_column("contracts_upstream", sa.Column("party_a_tax_no", sa.String(length=50), nullable=True))
    op.add_column("contracts_upstream", sa.Column("party_b_tax_no", sa.String(length=50), nullable=True))
    op.create_index("ix_contracts_upstream_party_a_tax_no", "contracts_upstream", ["party_a_tax_no"])
    op.create_index("ix_contracts_upstream_party_b_tax_no", "contracts_upstream", ["party_b_tax_no"])

    op.add_column("contracts_downstream", sa.Column("party_a_tax_no", sa.String(length=50), nullable=True))
    op.add_column("contracts_downstream", sa.Column("party_b_tax_no", sa.String(length=50), nullable=True))
    op.create_index("ix_contracts_downstream_party_a_tax_no", "contracts_downstream", ["party_a_tax_no"])
    op.create_index("ix_contracts_downstream_party_b_tax_no", "contracts_downstream", ["party_b_tax_no"])

    op.create_table(
        "invoice_import_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_number", sa.String(length=50), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("archive_file_path", sa.String(length=500), nullable=True),
        sa.Column("archive_file_key", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("parsed_items", sa.Integer(), nullable=False),
        sa.Column("failed_items", sa.Integer(), nullable=False),
        sa.Column("duplicate_items", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_import_batches_batch_number", "invoice_import_batches", ["batch_number"], unique=True)
    op.create_index("ix_invoice_import_batches_created_at", "invoice_import_batches", ["created_at"])
    op.create_index("ix_invoice_import_batches_status", "invoice_import_batches", ["status"])

    op.create_table(
        "invoice_import_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("source_archive_name", sa.String(length=255), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_code", sa.String(length=100), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("seller_name", sa.String(length=200), nullable=True),
        sa.Column("seller_tax_no", sa.String(length=50), nullable=True),
        sa.Column("buyer_name", sa.String(length=200), nullable=True),
        sa.Column("buyer_tax_no", sa.String(length=50), nullable=True),
        sa.Column("amount_without_tax", sa.Numeric(15, 2), nullable=True),
        sa.Column("tax_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("invoice_type", sa.String(length=100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("duplicate_of_item_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(length=50), nullable=False),
        sa.Column("parse_status", sa.String(length=50), nullable=False),
        sa.Column("match_status", sa.String(length=50), nullable=False),
        sa.Column("confirmation_status", sa.String(length=50), nullable=False),
        sa.Column("pdf_file_path", sa.String(length=500), nullable=True),
        sa.Column("pdf_file_key", sa.String(length=500), nullable=True),
        sa.Column("ofd_file_path", sa.String(length=500), nullable=True),
        sa.Column("ofd_file_key", sa.String(length=500), nullable=True),
        sa.Column("xml_file_path", sa.String(length=500), nullable=True),
        sa.Column("xml_file_key", sa.String(length=500), nullable=True),
        sa.Column("raw_xml", sa.Text(), nullable=True),
        sa.Column("parsed_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["invoice_import_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["duplicate_of_item_id"], ["invoice_import_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["batch_id", "invoice_number", "invoice_date", "seller_name", "seller_tax_no", "buyer_name", "buyer_tax_no", "dedupe_key", "direction", "parse_status", "match_status", "confirmation_status", "created_at"]:
        op.create_index(f"ix_invoice_import_items_{column}", "invoice_import_items", [column])
    op.create_index(
        "uq_invoice_import_items_active_dedupe",
        "invoice_import_items",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("duplicate_of_item_id IS NULL AND dedupe_key IS NOT NULL"),
    )

    op.create_table(
        "invoice_import_allocations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False),
        sa.Column("upstream_contract_id", sa.Integer(), nullable=True),
        sa.Column("downstream_contract_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("formal_invoice_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["downstream_contract_id"], ["contracts_downstream.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["item_id"], ["invoice_import_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upstream_contract_id"], ["contracts_upstream.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["item_id", "direction", "upstream_contract_id", "downstream_contract_id", "status", "created_at"]:
        op.create_index(f"ix_invoice_import_allocations_{column}", "invoice_import_allocations", [column])

    op.create_table(
        "invoice_import_match_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False),
        sa.Column("upstream_contract_id", sa.Integer(), nullable=True),
        sa.Column("downstream_contract_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("matched_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["downstream_contract_id"], ["contracts_downstream.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["invoice_import_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upstream_contract_id"], ["contracts_upstream.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["item_id", "direction", "upstream_contract_id", "downstream_contract_id", "created_at"]:
        op.create_index(f"ix_invoice_import_match_candidates_{column}", "invoice_import_match_candidates", [column])

    op.add_column("finance_upstream_invoices", sa.Column("source_import_item_id", sa.Integer(), nullable=True))
    op.add_column("finance_upstream_invoices", sa.Column("source_import_allocation_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_finance_upstream_invoices_source_import_item", "finance_upstream_invoices", "invoice_import_items", ["source_import_item_id"], ["id"])
    op.create_foreign_key("fk_finance_upstream_invoices_source_import_allocation", "finance_upstream_invoices", "invoice_import_allocations", ["source_import_allocation_id"], ["id"])
    op.create_index("ix_finance_upstream_invoices_source_import_item_id", "finance_upstream_invoices", ["source_import_item_id"])
    op.create_index("ix_finance_upstream_invoices_source_import_allocation_id", "finance_upstream_invoices", ["source_import_allocation_id"])

    op.add_column("finance_downstream_invoices", sa.Column("source_import_item_id", sa.Integer(), nullable=True))
    op.add_column("finance_downstream_invoices", sa.Column("source_import_allocation_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_finance_downstream_invoices_source_import_item", "finance_downstream_invoices", "invoice_import_items", ["source_import_item_id"], ["id"])
    op.create_foreign_key("fk_finance_downstream_invoices_source_import_allocation", "finance_downstream_invoices", "invoice_import_allocations", ["source_import_allocation_id"], ["id"])
    op.create_index("ix_finance_downstream_invoices_source_import_item_id", "finance_downstream_invoices", ["source_import_item_id"])
    op.create_index("ix_finance_downstream_invoices_source_import_allocation_id", "finance_downstream_invoices", ["source_import_allocation_id"])


def downgrade() -> None:
    conn = op.get_bind()

    def drop_source_columns(table_name: str) -> None:
        inspector = sa.inspect(conn)
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name in ("source_import_allocation_id", "source_import_item_id"):
            if column_name not in existing_columns:
                continue
            for foreign_key in inspector.get_foreign_keys(table_name):
                if foreign_key.get("constrained_columns") == [column_name] and foreign_key.get("name"):
                    op.drop_constraint(foreign_key["name"], table_name, type_="foreignkey")
            indexes = {index["name"] for index in sa.inspect(conn).get_indexes(table_name)}
            index_name = f"ix_{table_name}_{column_name}"
            if index_name in indexes:
                op.drop_index(index_name, table_name=table_name)
            op.drop_column(table_name, column_name)

    drop_source_columns("finance_downstream_invoices")
    drop_source_columns("finance_upstream_invoices")

    op.drop_table("invoice_import_match_candidates")
    op.drop_table("invoice_import_allocations")
    op.drop_table("invoice_import_items")
    op.drop_table("invoice_import_batches")

    for table_name in ("contracts_downstream", "contracts_upstream"):
        existing_columns = {column["name"] for column in sa.inspect(conn).get_columns(table_name)}
        for column_name in ("party_b_tax_no", "party_a_tax_no"):
            if column_name in existing_columns:
                index_name = f"ix_{table_name}_{column_name}"
                indexes = {index["name"] for index in sa.inspect(conn).get_indexes(table_name)}
                if index_name in indexes:
                    op.drop_index(index_name, table_name=table_name)
                op.drop_column(table_name, column_name)
