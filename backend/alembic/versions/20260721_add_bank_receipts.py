"""Add bank receipt import lifecycle tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260721_bank_receipts"
down_revision = "20260721_invoice_import_tax_rate"
branch_labels = None
depends_on = None

def upgrade():
    # The legacy empty-baseline revision creates current Base.metadata on a brand-new
    # database. In that path these tables and columns already exist by the time this
    # revision runs. Existing deployed databases do not have them and take the full
    # additive migration below.
    if "bank_receipt_batches" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("bank_receipt_batches", sa.Column("id", sa.Integer, primary_key=True), sa.Column("batch_number", sa.String(50), nullable=False, unique=True), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("status", sa.String(50), nullable=False, server_default="uploaded"), sa.Column("uploaded_by", sa.Integer, sa.ForeignKey("users.id")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_table("bank_receipt_items", sa.Column("id", sa.Integer, primary_key=True), sa.Column("batch_id", sa.Integer, sa.ForeignKey("bank_receipt_batches.id", ondelete="CASCADE"), nullable=False), sa.Column("source_filename", sa.String(255), nullable=False), sa.Column("file_path", sa.String(500)), sa.Column("file_key", sa.String(500)), sa.Column("sha256", sa.String(64), nullable=False), sa.Column("direction", sa.String(20), nullable=False, server_default="unknown"), sa.Column("transaction_at", sa.DateTime(timezone=True)), sa.Column("amount", sa.Numeric(15,2)), sa.Column("currency", sa.String(20), server_default="CNY"), sa.Column("payer_name", sa.String(200)), sa.Column("payer_account", sa.String(100)), sa.Column("payee_name", sa.String(200)), sa.Column("payee_account", sa.String(100)), sa.Column("summary", sa.String(500)), sa.Column("bank_serial_number", sa.String(150)), sa.Column("raw_mineru_result", postgresql.JSONB), sa.Column("parsed_payload", postgresql.JSONB), sa.Column("confidence", sa.Numeric(5,2)), sa.Column("status", sa.String(30), nullable=False, server_default="needs_review"), sa.Column("error_message", sa.Text), sa.Column("clear_reason", sa.String(300)), sa.Column("cleared_by", sa.Integer, sa.ForeignKey("users.id")), sa.Column("cleared_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("sha256", name="uq_bank_receipt_sha256"), sa.UniqueConstraint("bank_serial_number", name="uq_bank_receipt_serial"))
    op.create_table("bank_receipt_allocations", sa.Column("id", sa.Integer, primary_key=True), sa.Column("item_id", sa.Integer, sa.ForeignKey("bank_receipt_items.id", ondelete="CASCADE"), nullable=False), sa.Column("direction", sa.String(20), nullable=False), sa.Column("upstream_contract_id", sa.Integer, sa.ForeignKey("contracts_upstream.id", ondelete="RESTRICT")), sa.Column("downstream_contract_id", sa.Integer, sa.ForeignKey("contracts_downstream.id", ondelete="RESTRICT")), sa.Column("management_contract_id", sa.Integer, sa.ForeignKey("contracts_management.id", ondelete="RESTRICT")), sa.Column("amount", sa.Numeric(15,2), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="draft"), sa.Column("formal_record_id", sa.Integer), sa.Column("confirmed_by", sa.Integer, sa.ForeignKey("users.id")), sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    op.create_table("bank_receipt_match_candidates", sa.Column("id", sa.Integer, primary_key=True), sa.Column("item_id", sa.Integer, sa.ForeignKey("bank_receipt_items.id", ondelete="CASCADE"), nullable=False), sa.Column("direction", sa.String(20), nullable=False), sa.Column("contract_type", sa.String(20), nullable=False), sa.Column("contract_id", sa.Integer, nullable=False), sa.Column("score", sa.Integer, nullable=False, server_default="0"), sa.Column("matched_signals", postgresql.JSONB, nullable=False, server_default="{}"), sa.Column("contract_name", sa.String(500)))
    op.create_table("finance_zero_hour_payables",sa.Column("id",sa.Integer,primary_key=True),sa.Column("zero_hour_labor_id",sa.Integer,sa.ForeignKey("zero_hour_labor.id",ondelete="CASCADE"),nullable=False),sa.Column("category",sa.String(100),nullable=False),sa.Column("amount",sa.Numeric(15,2),nullable=False),sa.Column("expected_date",sa.Date),sa.Column("description",sa.String(300)),sa.Column("file_path",sa.String(500)),sa.Column("file_key",sa.String(500)),sa.Column("created_by",sa.Integer,sa.ForeignKey("users.id")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table("finance_zero_hour_invoices",sa.Column("id",sa.Integer,primary_key=True),sa.Column("zero_hour_labor_id",sa.Integer,sa.ForeignKey("zero_hour_labor.id",ondelete="CASCADE"),nullable=False),sa.Column("invoice_date",sa.Date,nullable=False),sa.Column("invoice_number",sa.String(100),nullable=False),sa.Column("amount",sa.Numeric(15,2),nullable=False),sa.Column("tax_amount",sa.Numeric(15,2),server_default="0"),sa.Column("supplier",sa.String(200)),sa.Column("file_path",sa.String(500)),sa.Column("file_key",sa.String(500)),sa.Column("status",sa.String(30),server_default="active"),sa.Column("source_import_item_id",sa.Integer,sa.ForeignKey("invoice_import_items.id")),sa.Column("created_by",sa.Integer,sa.ForeignKey("users.id")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_table("finance_zero_hour_payments",sa.Column("id",sa.Integer,primary_key=True),sa.Column("zero_hour_labor_id",sa.Integer,sa.ForeignKey("zero_hour_labor.id",ondelete="CASCADE"),nullable=False),sa.Column("payment_date",sa.Date,nullable=False),sa.Column("amount",sa.Numeric(15,2),nullable=False),sa.Column("payee_name",sa.String(200)),sa.Column("payee_account",sa.String(100)),sa.Column("payee_bank",sa.String(200)),sa.Column("payment_method",sa.String(50)),sa.Column("file_path",sa.String(500)),sa.Column("file_key",sa.String(500)),sa.Column("status",sa.String(30),server_default="active"),sa.Column("source_bank_receipt_item_id",sa.Integer,sa.ForeignKey("bank_receipt_items.id")),sa.Column("created_by",sa.Integer,sa.ForeignKey("users.id")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    for name, typ in [("ignored_reason",sa.String(300)),("ignored_by",sa.Integer),("ignored_at",sa.DateTime(timezone=True)),("clear_reason",sa.String(300)),("cleared_by",sa.Integer),("cleared_at",sa.DateTime(timezone=True)),("posting_version",sa.Integer)]: op.add_column("invoice_import_items",sa.Column(name,typ,nullable=False if name=="posting_version" else True,server_default="0" if name=="posting_version" else None))
    op.add_column("invoice_import_allocations",sa.Column("management_contract_id",sa.Integer,sa.ForeignKey("contracts_management.id",ondelete="RESTRICT"),nullable=True))
    formal_tables=("finance_upstream_receipts","finance_downstream_payments","finance_management_payments")
    receipt_source_indexes={"finance_upstream_receipts":"uq_up_receipt_bank_alloc","finance_downstream_payments":"uq_down_payment_bank_alloc","finance_management_payments":"uq_mgmt_payment_bank_alloc"}
    for table in formal_tables:
        op.add_column(table,sa.Column("source_bank_receipt_item_id",sa.Integer,sa.ForeignKey("bank_receipt_items.id"),nullable=True)); op.add_column(table,sa.Column("source_bank_receipt_allocation_id",sa.Integer,sa.ForeignKey("bank_receipt_allocations.id"),nullable=True)); op.add_column(table,sa.Column("bank_serial_number",sa.String(150),nullable=True)); op.add_column(table,sa.Column("transaction_at",sa.DateTime(timezone=True),nullable=True)); op.create_index(receipt_source_indexes[table],table,["source_bank_receipt_allocation_id"],unique=True)
        op.add_column(table,sa.Column("posting_status",sa.String(20),nullable=False,server_default="active")); op.add_column(table,sa.Column("cleared_at",sa.DateTime(timezone=True))); op.add_column(table,sa.Column("clear_reason",sa.String(300))); op.add_column(table,sa.Column("original_amount",sa.Numeric(15,2)))
    for table in ("finance_management_invoices",):
        op.add_column(table,sa.Column("source_import_item_id",sa.Integer,sa.ForeignKey("invoice_import_items.id"),nullable=True)); op.add_column(table,sa.Column("source_import_allocation_id",sa.Integer,sa.ForeignKey("invoice_import_allocations.id"),nullable=True)); op.create_index(f"ix_{table}_source_import_allocation_id",table,["source_import_allocation_id"],unique=True)
    for table in ("finance_upstream_invoices","finance_downstream_invoices","finance_management_invoices"):
        op.add_column(table,sa.Column("posting_status",sa.String(20),nullable=False,server_default="active")); op.add_column(table,sa.Column("cleared_at",sa.DateTime(timezone=True))); op.add_column(table,sa.Column("clear_reason",sa.String(300))); op.add_column(table,sa.Column("original_amount",sa.Numeric(15,2)))
    for table, cols in {"bank_receipt_batches": ["status", "created_at"], "bank_receipt_items": ["batch_id", "sha256", "direction", "status", "transaction_at"], "bank_receipt_allocations": ["item_id"], "bank_receipt_match_candidates": ["item_id"]}.items():
        for col in cols: op.create_index(f"ix_{table}_{col}", table, [col])

def downgrade():
    # Paired with the empty-baseline compatibility branch in upgrade(): when the
    # baseline created current metadata, this revision did not add any objects.
    if "uq_up_receipt_bank_alloc" not in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("finance_upstream_receipts")}:
        return
    op.drop_table("finance_zero_hour_payments")
    op.drop_table("finance_zero_hour_invoices")
    op.drop_table("finance_zero_hour_payables")
    for table in ("finance_upstream_invoices","finance_downstream_invoices","finance_management_invoices"):
        op.drop_column(table,"original_amount"); op.drop_column(table,"clear_reason"); op.drop_column(table,"cleared_at"); op.drop_column(table,"posting_status")
    op.drop_index("ix_finance_management_invoices_source_import_allocation_id",table_name="finance_management_invoices")
    op.drop_column("finance_management_invoices","source_import_allocation_id"); op.drop_column("finance_management_invoices","source_import_item_id")
    for table in ("finance_upstream_receipts","finance_downstream_payments","finance_management_payments"):
        op.drop_column(table,"original_amount"); op.drop_column(table,"clear_reason"); op.drop_column(table,"cleared_at"); op.drop_column(table,"posting_status")
        receipt_source_indexes={"finance_upstream_receipts":"uq_up_receipt_bank_alloc","finance_downstream_payments":"uq_down_payment_bank_alloc","finance_management_payments":"uq_mgmt_payment_bank_alloc"}
        op.drop_index(receipt_source_indexes[table],table_name=table)
        op.drop_column(table,"transaction_at"); op.drop_column(table,"bank_serial_number"); op.drop_column(table,"source_bank_receipt_allocation_id"); op.drop_column(table,"source_bank_receipt_item_id")
    op.drop_column("invoice_import_allocations","management_contract_id")
    for name in ("posting_version","cleared_at","cleared_by","clear_reason","ignored_at","ignored_by","ignored_reason"): op.drop_column("invoice_import_items",name)
    op.drop_table("bank_receipt_match_candidates")
    op.drop_table("bank_receipt_allocations")
    op.drop_table("bank_receipt_items")
    op.drop_table("bank_receipt_batches")
