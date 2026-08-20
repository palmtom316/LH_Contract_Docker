"""Warehouse P1 traceability: batches, units, ledger/report filters.

Revision ID: 20260819_warehouse_p1_trace
Revises: 20260819_warehouse_p0_controls
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260819_warehouse_p1_trace"
down_revision = "20260819_warehouse_p0_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    material_columns = {
        column["name"] for column in inspector.get_columns("warehouse_materials")
    }
    if "quantity_scale" in material_columns and "warehouse_units" in inspector.get_table_names():
        return
    op.add_column(
        "warehouse_materials",
        sa.Column("quantity_scale", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "warehouse_materials",
        sa.Column("tracks_batch", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "warehouse_materials",
        sa.Column("tracks_serial", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "warehouse_materials",
        sa.Column("shelf_life_days", sa.Integer(), nullable=True),
    )

    op.add_column(
        "warehouse_document_lines",
        sa.Column("batch_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_document_lines",
        sa.Column("serial_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_document_lines",
        sa.Column("heat_no", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "warehouse_document_lines",
        sa.Column("production_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "warehouse_document_lines",
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_warehouse_document_lines_batch_no",
        "warehouse_document_lines",
        ["batch_no"],
    )
    op.create_index(
        "ix_warehouse_document_lines_serial_no",
        "warehouse_document_lines",
        ["serial_no"],
    )

    op.add_column(
        "warehouse_ledger_entries",
        sa.Column("batch_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_ledger_entries",
        sa.Column("serial_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_ledger_entries",
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )
    op.drop_constraint(
        "uq_warehouse_ledger_line_dimension",
        "warehouse_ledger_entries",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_warehouse_ledger_line_dimension",
        "warehouse_ledger_entries",
        [
            "document_line_id",
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
            "batch_no",
            "serial_no",
        ],
    )
    op.create_index(
        "ix_warehouse_ledger_entries_batch_no",
        "warehouse_ledger_entries",
        ["batch_no"],
    )
    op.create_index(
        "ix_warehouse_ledger_entries_serial_no",
        "warehouse_ledger_entries",
        ["serial_no"],
    )
    op.create_index(
        "ix_warehouse_ledger_entries_expiry_date",
        "warehouse_ledger_entries",
        ["expiry_date"],
    )

    op.add_column(
        "warehouse_stock_balances",
        sa.Column("batch_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_stock_balances",
        sa.Column("serial_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_stock_balances",
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )
    op.drop_constraint(
        "uq_warehouse_stock_dimension", "warehouse_stock_balances", type_="unique"
    )
    op.create_unique_constraint(
        "uq_warehouse_stock_dimension",
        "warehouse_stock_balances",
        [
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
            "batch_no",
            "serial_no",
        ],
    )
    op.create_index(
        "ix_warehouse_stock_balances_batch_no",
        "warehouse_stock_balances",
        ["batch_no"],
    )
    op.create_index(
        "ix_warehouse_stock_balances_serial_no",
        "warehouse_stock_balances",
        ["serial_no"],
    )
    op.create_index(
        "ix_warehouse_stock_balances_expiry_date",
        "warehouse_stock_balances",
        ["expiry_date"],
    )

    op.add_column(
        "warehouse_count_lines",
        sa.Column("batch_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_count_lines",
        sa.Column("serial_no", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "warehouse_count_lines",
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )
    op.drop_constraint(
        "uq_warehouse_count_line_dimension",
        "warehouse_count_lines",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_warehouse_count_line_dimension",
        "warehouse_count_lines",
        [
            "count_id",
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
            "batch_no",
            "serial_no",
        ],
    )

    op.create_table(
        "warehouse_units",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("aliases", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_warehouse_unit_code"),
    )
    op.create_table(
        "warehouse_unit_conversions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("from_unit_id", sa.Integer(), nullable=False),
        sa.Column("to_unit_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Numeric(18, 6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("factor > 0", name="ck_warehouse_unit_conversion_factor"),
        sa.ForeignKeyConstraint(
            ["from_unit_id"], ["warehouse_units.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["to_unit_id"], ["warehouse_units.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_unit_id", "to_unit_id", name="uq_warehouse_unit_conversion"
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO warehouse_units (code, name, aliases)
            VALUES
              ('m', '米', '米,M,公尺'),
              ('pc', '件', '件,个,只'),
              ('kg', '千克', '千克,公斤,kg,KG'),
              ('t', '吨', '吨,T'),
              ('roll', '圈', '圈,卷'),
              ('box', '箱', '箱'),
              ('bundle', '捆', '捆')
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO warehouse_unit_conversions (from_unit_id, to_unit_id, factor)
            SELECT a.id, b.id, 1000
            FROM warehouse_units a, warehouse_units b
            WHERE a.code = 't' AND b.code = 'kg'
            """
        )
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "quantity_scale" not in {
        column["name"] for column in inspector.get_columns("warehouse_materials")
    }:
        return
    op.drop_table("warehouse_unit_conversions")
    op.drop_table("warehouse_units")

    op.drop_constraint(
        "uq_warehouse_count_line_dimension",
        "warehouse_count_lines",
        type_="unique",
    )
    op.drop_column("warehouse_count_lines", "expiry_date")
    op.drop_column("warehouse_count_lines", "serial_no")
    op.drop_column("warehouse_count_lines", "batch_no")
    op.create_unique_constraint(
        "uq_warehouse_count_line_dimension",
        "warehouse_count_lines",
        ["count_id", "warehouse_id", "location_id", "project_id", "material_id"],
    )

    op.drop_index(
        "ix_warehouse_stock_balances_expiry_date", table_name="warehouse_stock_balances"
    )
    op.drop_index(
        "ix_warehouse_stock_balances_serial_no", table_name="warehouse_stock_balances"
    )
    op.drop_index(
        "ix_warehouse_stock_balances_batch_no", table_name="warehouse_stock_balances"
    )
    op.drop_constraint(
        "uq_warehouse_stock_dimension", "warehouse_stock_balances", type_="unique"
    )
    op.drop_column("warehouse_stock_balances", "expiry_date")
    op.drop_column("warehouse_stock_balances", "serial_no")
    op.drop_column("warehouse_stock_balances", "batch_no")
    op.create_unique_constraint(
        "uq_warehouse_stock_dimension",
        "warehouse_stock_balances",
        ["warehouse_id", "location_id", "project_id", "material_id"],
    )

    op.drop_index(
        "ix_warehouse_ledger_entries_expiry_date", table_name="warehouse_ledger_entries"
    )
    op.drop_index(
        "ix_warehouse_ledger_entries_serial_no", table_name="warehouse_ledger_entries"
    )
    op.drop_index(
        "ix_warehouse_ledger_entries_batch_no", table_name="warehouse_ledger_entries"
    )
    op.drop_constraint(
        "uq_warehouse_ledger_line_dimension",
        "warehouse_ledger_entries",
        type_="unique",
    )
    op.drop_column("warehouse_ledger_entries", "expiry_date")
    op.drop_column("warehouse_ledger_entries", "serial_no")
    op.drop_column("warehouse_ledger_entries", "batch_no")
    op.create_unique_constraint(
        "uq_warehouse_ledger_line_dimension",
        "warehouse_ledger_entries",
        [
            "document_line_id",
            "warehouse_id",
            "location_id",
            "project_id",
            "material_id",
        ],
    )

    op.drop_index(
        "ix_warehouse_document_lines_serial_no", table_name="warehouse_document_lines"
    )
    op.drop_index(
        "ix_warehouse_document_lines_batch_no", table_name="warehouse_document_lines"
    )
    op.drop_column("warehouse_document_lines", "expiry_date")
    op.drop_column("warehouse_document_lines", "production_date")
    op.drop_column("warehouse_document_lines", "heat_no")
    op.drop_column("warehouse_document_lines", "serial_no")
    op.drop_column("warehouse_document_lines", "batch_no")

    op.drop_column("warehouse_materials", "shelf_life_days")
    op.drop_column("warehouse_materials", "tracks_serial")
    op.drop_column("warehouse_materials", "tracks_batch")
    op.drop_column("warehouse_materials", "quantity_scale")
