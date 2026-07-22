"""Add durable import leases and zero-hour allocation provenance."""

from alembic import op
import sqlalchemy as sa

revision = "20260722_durable_import_jobs"
down_revision = "20260722_reconcile_finance_columns"
branch_labels = None
depends_on = None


def _add_columns(table, definitions):
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns(table)}
    for name, column in definitions:
        if name not in existing:
            op.add_column(table, column)


def _ensure_index(table, name, columns, unique=False):
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes(table)}
    constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints(table)
    }
    if name not in indexes and name not in constraints:
        op.create_index(name, table, columns, unique=unique)


def upgrade():
    for table in ("invoice_import_batches", "bank_receipt_batches"):
        _add_columns(
            table,
            [
                (
                    "job_attempts",
                    sa.Column(
                        "job_attempts", sa.Integer(), nullable=False, server_default="0"
                    ),
                ),
                (
                    "job_next_attempt_at",
                    sa.Column("job_next_attempt_at", sa.DateTime(timezone=True)),
                ),
                (
                    "job_lease_until",
                    sa.Column("job_lease_until", sa.DateTime(timezone=True)),
                ),
                ("job_worker_token", sa.Column("job_worker_token", sa.String(64))),
                ("job_last_error", sa.Column("job_last_error", sa.Text())),
            ],
        )
        _ensure_index(table, f"ix_{table}_job_next_attempt_at", ["job_next_attempt_at"])
        _ensure_index(table, f"ix_{table}_job_lease_until", ["job_lease_until"])
        _ensure_index(table, f"ix_{table}_job_worker_token", ["job_worker_token"])

    _add_columns(
        "finance_zero_hour_invoices",
        [
            (
                "source_import_allocation_id",
                sa.Column(
                    "source_import_allocation_id",
                    sa.Integer(),
                    sa.ForeignKey("invoice_import_allocations.id"),
                ),
            ),
        ],
    )
    _add_columns(
        "finance_zero_hour_payments",
        [
            (
                "source_bank_receipt_allocation_id",
                sa.Column(
                    "source_bank_receipt_allocation_id",
                    sa.Integer(),
                    sa.ForeignKey("bank_receipt_allocations.id"),
                ),
            ),
        ],
    )
    _ensure_index(
        "finance_zero_hour_invoices",
        "uq_zero_hour_invoice_import_alloc",
        ["source_import_allocation_id"],
        unique=True,
    )
    _ensure_index(
        "finance_zero_hour_payments",
        "uq_zero_hour_payment_receipt_alloc",
        ["source_bank_receipt_allocation_id"],
        unique=True,
    )
    _add_columns(
        "invoice_import_allocations",
        [
            (
                "zero_hour_labor_id",
                sa.Column(
                    "zero_hour_labor_id",
                    sa.Integer(),
                    sa.ForeignKey("zero_hour_labor.id", ondelete="RESTRICT"),
                ),
            ),
        ],
    )
    _add_columns(
        "bank_receipt_allocations",
        [
            (
                "zero_hour_labor_id",
                sa.Column(
                    "zero_hour_labor_id",
                    sa.Integer(),
                    sa.ForeignKey("zero_hour_labor.id", ondelete="RESTRICT"),
                ),
            ),
        ],
    )
    _ensure_index(
        "invoice_import_allocations",
        "ix_invoice_import_allocations_zero_hour_labor_id",
        ["zero_hour_labor_id"],
    )
    _ensure_index(
        "bank_receipt_allocations",
        "ix_bank_receipt_allocations_zero_hour_labor_id",
        ["zero_hour_labor_id"],
    )


def downgrade():
    # Keep provenance columns during downgrade; deleting them would destroy audit links.
    pass
