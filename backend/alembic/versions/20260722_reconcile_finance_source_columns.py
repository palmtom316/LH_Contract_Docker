"""Reconcile release 1.9 source and lifecycle columns on baseline-created databases."""

from alembic import op
import sqlalchemy as sa

revision = "20260722_reconcile_finance_columns"
down_revision = "20260722_receipt_ignore"
branch_labels = None
depends_on = None


def _add_columns(table, definitions):
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns(table)}
    for name, column in definitions:
        if name not in existing:
            op.add_column(table, column)


def _ensure_unique_index(table, name, column):
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes(table)}
    constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints(table)
    }
    if name not in indexes and name not in constraints:
        op.create_index(name, table, [column], unique=True)


def upgrade():
    # Some 1.8 installations use Alembic's default VARCHAR(32); this revision id
    # is longer, so widen the metadata column before Alembic records the revision.
    inspector = sa.inspect(op.get_bind())
    if "alembic_version" in inspector.get_table_names():
        op.alter_column(
            "alembic_version",
            "version_num",
            type_=sa.String(255),
            existing_type=sa.String(32),
        )
    _add_columns(
        "invoice_import_items",
        [
            ("ignored_reason", sa.Column("ignored_reason", sa.String(300))),
            (
                "ignored_by",
                sa.Column("ignored_by", sa.Integer(), sa.ForeignKey("users.id")),
            ),
            ("ignored_at", sa.Column("ignored_at", sa.DateTime(timezone=True))),
            ("clear_reason", sa.Column("clear_reason", sa.String(300))),
            (
                "cleared_by",
                sa.Column("cleared_by", sa.Integer(), sa.ForeignKey("users.id")),
            ),
            ("cleared_at", sa.Column("cleared_at", sa.DateTime(timezone=True))),
            (
                "posting_version",
                sa.Column(
                    "posting_version", sa.Integer(), nullable=False, server_default="0"
                ),
            ),
        ],
    )
    _add_columns(
        "invoice_import_allocations",
        [
            (
                "management_contract_id",
                sa.Column(
                    "management_contract_id",
                    sa.Integer(),
                    sa.ForeignKey("contracts_management.id", ondelete="RESTRICT"),
                ),
            )
        ],
    )
    _add_columns(
        "bank_receipt_items",
        [
            (
                "posting_version",
                sa.Column(
                    "posting_version", sa.Integer(), nullable=False, server_default="0"
                ),
            ),
        ],
    )
    for table in (
        "finance_upstream_invoices",
        "finance_downstream_invoices",
        "finance_management_invoices",
    ):
        _add_columns(
            table,
            [
                (
                    "source_import_item_id",
                    sa.Column(
                        "source_import_item_id",
                        sa.Integer(),
                        sa.ForeignKey("invoice_import_items.id"),
                    ),
                ),
                (
                    "source_import_allocation_id",
                    sa.Column(
                        "source_import_allocation_id",
                        sa.Integer(),
                        sa.ForeignKey("invoice_import_allocations.id"),
                    ),
                ),
                (
                    "posting_status",
                    sa.Column(
                        "posting_status",
                        sa.String(20),
                        nullable=False,
                        server_default="active",
                    ),
                ),
                ("cleared_at", sa.Column("cleared_at", sa.DateTime(timezone=True))),
                ("clear_reason", sa.Column("clear_reason", sa.String(300))),
                ("original_amount", sa.Column("original_amount", sa.Numeric(15, 2))),
            ],
        )
        _ensure_unique_index(
            table,
            f"ix_{table}_source_import_allocation_id",
            "source_import_allocation_id",
        )
    for table in (
        "finance_upstream_receipts",
        "finance_downstream_payments",
        "finance_management_payments",
    ):
        _add_columns(
            table,
            [
                (
                    "source_bank_receipt_item_id",
                    sa.Column(
                        "source_bank_receipt_item_id",
                        sa.Integer(),
                        sa.ForeignKey("bank_receipt_items.id"),
                    ),
                ),
                (
                    "source_bank_receipt_allocation_id",
                    sa.Column(
                        "source_bank_receipt_allocation_id",
                        sa.Integer(),
                        sa.ForeignKey("bank_receipt_allocations.id"),
                    ),
                ),
                ("bank_serial_number", sa.Column("bank_serial_number", sa.String(150))),
                (
                    "transaction_at",
                    sa.Column("transaction_at", sa.DateTime(timezone=True)),
                ),
                (
                    "posting_status",
                    sa.Column(
                        "posting_status",
                        sa.String(20),
                        nullable=False,
                        server_default="active",
                    ),
                ),
                ("cleared_at", sa.Column("cleared_at", sa.DateTime(timezone=True))),
                ("clear_reason", sa.Column("clear_reason", sa.String(300))),
                ("original_amount", sa.Column("original_amount", sa.Numeric(15, 2))),
            ],
        )
    for table, name in {
        "finance_upstream_receipts": "uq_up_receipt_bank_alloc",
        "finance_downstream_payments": "uq_down_payment_bank_alloc",
        "finance_management_payments": "uq_mgmt_payment_bank_alloc",
    }.items():
        _ensure_unique_index(table, name, "source_bank_receipt_allocation_id")


def downgrade():
    # Additive reconciliation is intentionally not destructive on downgrade.
    pass
