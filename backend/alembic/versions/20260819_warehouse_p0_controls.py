"""Warehouse P0 controls: periods, count snapshot, supplements, vouchers.

Revision ID: 20260819_warehouse_p0_controls
Revises: 20260813_warehouse_attachments_and_types
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260819_warehouse_p0_controls"
down_revision = "20260813_warehouse_attachments_and_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    document_columns = {
        column["name"] for column in inspector.get_columns("warehouse_documents")
    }
    if "supplier_name" in document_columns and "warehouse_periods" in inspector.get_table_names():
        return
    op.add_column(
        "warehouse_documents",
        sa.Column("supplier_name", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("purchase_order_no", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("delivery_note_no", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("acceptance_no", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("acceptor", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("qc_result", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("manufacturer", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("batch_no", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("requisition_no", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("work_package", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("crew_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("requester_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("receiver_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column(
            "signed_off",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_status", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_weight", sa.Numeric(18, 4), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_assessed_value", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_disposal_method", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_recycler", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_residual_value", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "warehouse_documents",
        sa.Column("scrap_settled_by", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_warehouse_documents_scrap_status",
        "warehouse_documents",
        ["scrap_status"],
    )
    op.create_foreign_key(
        "fk_warehouse_documents_scrap_settled_by",
        "warehouse_documents",
        "users",
        ["scrap_settled_by"],
        ["id"],
    )

    op.add_column(
        "warehouse_counts",
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "warehouse_counts",
        sa.Column(
            "snapshot_source",
            sa.String(length=32),
            nullable=False,
            server_default="stock_balances",
        ),
    )
    op.add_column("warehouse_counts", sa.Column("void_reason", sa.Text(), nullable=True))
    op.add_column(
        "warehouse_counts", sa.Column("review_notes", sa.Text(), nullable=True)
    )
    op.add_column(
        "warehouse_counts", sa.Column("reviewed_by", sa.Integer(), nullable=True)
    )
    op.add_column(
        "warehouse_counts", sa.Column("voided_by", sa.Integer(), nullable=True)
    )
    op.add_column(
        "warehouse_counts",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "warehouse_counts",
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "warehouse_counts",
        sa.Column("reopened_from_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_warehouse_counts_reviewed_by",
        "warehouse_counts",
        "users",
        ["reviewed_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_warehouse_counts_voided_by",
        "warehouse_counts",
        "users",
        ["voided_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_warehouse_counts_reopened_from",
        "warehouse_counts",
        "warehouse_counts",
        ["reopened_from_id"],
        ["id"],
    )
    op.add_column(
        "warehouse_count_lines",
        sa.Column(
            "variance_reviewed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "warehouse_count_lines",
        sa.Column("variance_note", sa.Text(), nullable=True),
    )

    op.add_column(
        "warehouse_business_supplements",
        sa.Column(
            "line_key",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "warehouse_business_supplements",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "warehouse_business_supplements",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.execute(
        sa.text(
            "UPDATE warehouse_business_supplements "
            "SET line_key = COALESCE(document_line_id, 0)"
        )
    )
    op.create_unique_constraint(
        "uq_warehouse_supplement_document_line",
        "warehouse_business_supplements",
        ["document_id", "line_key"],
    )
    op.create_check_constraint(
        "ck_warehouse_supplement_unit_price_non_negative",
        "warehouse_business_supplements",
        "unit_price IS NULL OR unit_price >= 0",
    )
    op.create_check_constraint(
        "ck_warehouse_supplement_amount_non_negative",
        "warehouse_business_supplements",
        "amount IS NULL OR amount >= 0",
    )
    op.create_check_constraint(
        "ck_warehouse_supplement_weigh_in_non_negative",
        "warehouse_business_supplements",
        "weigh_in IS NULL OR weigh_in >= 0",
    )
    op.create_check_constraint(
        "ck_warehouse_supplement_residual_non_negative",
        "warehouse_business_supplements",
        "residual_value IS NULL OR residual_value >= 0",
    )

    op.create_table(
        "warehouse_business_supplement_histories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplement_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("document_line_id", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["supplement_id"],
            ["warehouse_business_supplements.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["warehouse_documents.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supplement_id",
            "version",
            name="uq_warehouse_supplement_history_version",
        ),
    )
    op.create_index(
        "ix_warehouse_business_supplement_histories_supplement_id",
        "warehouse_business_supplement_histories",
        ["supplement_id"],
    )
    op.create_index(
        "ix_warehouse_business_supplement_histories_document_id",
        "warehouse_business_supplement_histories",
        ["document_id"],
    )

    op.create_table(
        "warehouse_periods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("closed_by", sa.Integer(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopened_by", sa.Integer(), nullable=True),
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopen_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "month >= 1 AND month <= 12", name="ck_warehouse_period_month"
        ),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reopened_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "month", name="uq_warehouse_period_year_month"),
    )
    op.create_index("ix_warehouse_periods_year", "warehouse_periods", ["year"])
    op.create_index("ix_warehouse_periods_status", "warehouse_periods", ["status"])

    op.create_table(
        "warehouse_balance_repairs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "dry_run", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "repaired", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "dimensions", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "mismatches", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("differences", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "supplier_name" not in {
        column["name"] for column in inspector.get_columns("warehouse_documents")
    }:
        return
    op.drop_table("warehouse_balance_repairs")
    op.drop_index("ix_warehouse_periods_status", table_name="warehouse_periods")
    op.drop_index("ix_warehouse_periods_year", table_name="warehouse_periods")
    op.drop_table("warehouse_periods")
    op.drop_index(
        "ix_warehouse_business_supplement_histories_document_id",
        table_name="warehouse_business_supplement_histories",
    )
    op.drop_index(
        "ix_warehouse_business_supplement_histories_supplement_id",
        table_name="warehouse_business_supplement_histories",
    )
    op.drop_table("warehouse_business_supplement_histories")

    op.drop_constraint(
        "ck_warehouse_supplement_residual_non_negative",
        "warehouse_business_supplements",
        type_="check",
    )
    op.drop_constraint(
        "ck_warehouse_supplement_weigh_in_non_negative",
        "warehouse_business_supplements",
        type_="check",
    )
    op.drop_constraint(
        "ck_warehouse_supplement_amount_non_negative",
        "warehouse_business_supplements",
        type_="check",
    )
    op.drop_constraint(
        "ck_warehouse_supplement_unit_price_non_negative",
        "warehouse_business_supplements",
        type_="check",
    )
    op.drop_constraint(
        "uq_warehouse_supplement_document_line",
        "warehouse_business_supplements",
        type_="unique",
    )
    op.drop_column("warehouse_business_supplements", "created_at")
    op.drop_column("warehouse_business_supplements", "version")
    op.drop_column("warehouse_business_supplements", "line_key")

    op.drop_column("warehouse_count_lines", "variance_note")
    op.drop_column("warehouse_count_lines", "variance_reviewed")
    op.drop_constraint(
        "fk_warehouse_counts_reopened_from", "warehouse_counts", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_warehouse_counts_voided_by", "warehouse_counts", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_warehouse_counts_reviewed_by", "warehouse_counts", type_="foreignkey"
    )
    op.drop_column("warehouse_counts", "reopened_from_id")
    op.drop_column("warehouse_counts", "voided_at")
    op.drop_column("warehouse_counts", "reviewed_at")
    op.drop_column("warehouse_counts", "voided_by")
    op.drop_column("warehouse_counts", "reviewed_by")
    op.drop_column("warehouse_counts", "review_notes")
    op.drop_column("warehouse_counts", "void_reason")
    op.drop_column("warehouse_counts", "snapshot_source")
    op.drop_column("warehouse_counts", "snapshot_at")

    op.drop_constraint(
        "fk_warehouse_documents_scrap_settled_by",
        "warehouse_documents",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_warehouse_documents_scrap_status", table_name="warehouse_documents"
    )
    for column in (
        "scrap_settled_by",
        "scrap_settled_at",
        "scrap_residual_value",
        "scrap_recycler",
        "scrap_disposal_method",
        "scrap_assessed_value",
        "scrap_weight",
        "scrap_status",
        "signed_off",
        "receiver_name",
        "requester_name",
        "crew_name",
        "work_package",
        "requisition_no",
        "batch_no",
        "manufacturer",
        "qc_result",
        "acceptor",
        "acceptance_no",
        "delivery_note_no",
        "purchase_order_no",
        "supplier_name",
    ):
        op.drop_column("warehouse_documents", column)
