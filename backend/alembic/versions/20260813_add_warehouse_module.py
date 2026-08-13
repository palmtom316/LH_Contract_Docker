"""Add warehouse management module.

Revision ID: 20260813_add_warehouse_module
Revises: 20260725_refresh_token_timestamps_utc
Create Date: 2026-08-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_add_warehouse_module"
down_revision = "20260725_refresh_token_timestamps_utc"
branch_labels = None
depends_on = None


WAREHOUSE_TABLES = (
    "warehouse_business_supplements",
    "warehouse_count_lines",
    "warehouse_counts",
    "warehouse_ledger_entries",
    "warehouse_document_lines",
    "warehouse_documents",
    "warehouse_stock_balances",
    "warehouse_user_scopes",
    "warehouse_document_counters",
    "warehouse_code_counters",
    "warehouse_materials",
    "warehouse_projects",
    "warehouse_locations",
    "warehouse_warehouses",
)


def _add_userrole_values(conn) -> None:
    if conn.dialect.name != "postgresql":
        return
    existing = {
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT enumlabel FROM pg_enum e "
                "JOIN pg_type t ON t.oid = e.enumtypid "
                "WHERE t.typname = 'userrole'"
            )
        )
    }
    if not existing:
        return
    for value in ("WAREHOUSE_ADMIN", "COMPANY_STOREKEEPER"):
        if value not in existing:
            conn.execute(sa.text(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{value}'"))


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())
    _add_userrole_values(conn)

    if "warehouse_warehouses" not in existing_tables:
        op.create_table(
            "warehouse_warehouses",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("address", sa.String(length=255), nullable=True),
            sa.Column("manager_name", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
            sa.UniqueConstraint("name"),
        )
        op.create_index("ix_warehouse_warehouses_code", "warehouse_warehouses", ["code"])
        op.create_index("ix_warehouse_warehouses_name", "warehouse_warehouses", ["name"])

    if "warehouse_locations" not in existing_tables:
        op.create_table(
            "warehouse_locations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse_warehouses.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("warehouse_id", "code", name="uq_warehouse_location_code"),
        )
        op.create_index("ix_warehouse_locations_warehouse_id", "warehouse_locations", ["warehouse_id"])

    if "warehouse_projects" not in existing_tables:
        op.create_table(
            "warehouse_projects",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("upstream_contract_id", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["upstream_contract_id"], ["contracts_upstream.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
        op.create_index("ix_warehouse_projects_code", "warehouse_projects", ["code"])
        op.create_index("ix_warehouse_projects_name", "warehouse_projects", ["name"])

    if "warehouse_materials" not in existing_tables:
        op.create_table(
            "warehouse_materials",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("legacy_code", sa.String(length=50), nullable=True),
            sa.Column("category", sa.String(length=8), nullable=False),
            sa.Column("supply_type", sa.String(length=8), nullable=False),
            sa.Column("condition", sa.String(length=16), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("brand", sa.String(length=100), nullable=False, server_default=""),
            sa.Column("specification", sa.String(length=200), nullable=False, server_default=""),
            sa.Column("unit", sa.String(length=20), nullable=False),
            sa.Column("minimum_stock", sa.Numeric(18, 4), nullable=False, server_default="0"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("identity_key", sa.String(length=64), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
            sa.UniqueConstraint("identity_key", name="uq_warehouse_material_identity"),
        )
        op.create_index("ix_warehouse_materials_code", "warehouse_materials", ["code"])
        op.create_index("ix_warehouse_materials_name", "warehouse_materials", ["name"])
        op.create_index("ix_warehouse_materials_category", "warehouse_materials", ["category"])
        op.create_index("ix_warehouse_materials_supply_type", "warehouse_materials", ["supply_type"])

    if "warehouse_code_counters" not in existing_tables:
        op.create_table(
            "warehouse_code_counters",
            sa.Column("category", sa.String(length=8), nullable=False),
            sa.Column("supply_condition", sa.String(length=8), nullable=False),
            sa.Column("next_number", sa.Integer(), nullable=False, server_default="1"),
            sa.PrimaryKeyConstraint("category", "supply_condition"),
        )

    if "warehouse_document_counters" not in existing_tables:
        op.create_table(
            "warehouse_document_counters",
            sa.Column("prefix", sa.String(length=8), nullable=False),
            sa.Column("occurred_on", sa.Date(), nullable=False),
            sa.Column("next_number", sa.Integer(), nullable=False, server_default="1"),
            sa.PrimaryKeyConstraint("prefix", "occurred_on"),
        )

    if "warehouse_user_scopes" not in existing_tables:
        op.create_table(
            "warehouse_user_scopes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse_warehouses.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "warehouse_id", name="uq_warehouse_user_scope"),
        )
        op.create_index("ix_warehouse_user_scopes_user_id", "warehouse_user_scopes", ["user_id"])
        op.create_index("ix_warehouse_user_scopes_warehouse_id", "warehouse_user_scopes", ["warehouse_id"])

    if "warehouse_documents" not in existing_tables:
        op.create_table(
            "warehouse_documents",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_no", sa.String(length=40), nullable=False),
            sa.Column("document_type", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="POSTED"),
            sa.Column("occurred_on", sa.Date(), nullable=False),
            sa.Column("business_type", sa.String(length=32), nullable=True),
            sa.Column("reference_no", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("handler", sa.String(length=100), nullable=False),
            sa.Column("idempotency_key", sa.String(length=80), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("posted_by", sa.Integer(), nullable=True),
            sa.Column("voided_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("void_reason", sa.Text(), nullable=True),
            sa.Column("reversed_document_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["posted_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["reversed_document_id"], ["warehouse_documents.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("document_no"),
            sa.UniqueConstraint("created_by", "idempotency_key", name="uq_warehouse_document_idempotency"),
        )
        op.create_index("ix_warehouse_documents_document_no", "warehouse_documents", ["document_no"])
        op.create_index("ix_warehouse_documents_type", "warehouse_documents", ["document_type"])
        op.create_index("ix_warehouse_documents_status", "warehouse_documents", ["status"])
        op.create_index("ix_warehouse_documents_occurred_on", "warehouse_documents", ["occurred_on"])

    if "warehouse_document_lines" not in existing_tables:
        op.create_table(
            "warehouse_document_lines",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("line_no", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
            sa.Column("source_warehouse_id", sa.Integer(), nullable=True),
            sa.Column("source_location_id", sa.Integer(), nullable=True),
            sa.Column("source_project_id", sa.Integer(), nullable=True),
            sa.Column("target_warehouse_id", sa.Integer(), nullable=True),
            sa.Column("target_location_id", sa.Integer(), nullable=True),
            sa.Column("target_project_id", sa.Integer(), nullable=True),
            sa.Column("original_document_line_id", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.CheckConstraint("quantity > 0", name="ck_warehouse_document_line_qty_positive"),
            sa.ForeignKeyConstraint(["document_id"], ["warehouse_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["material_id"], ["warehouse_materials.id"]),
            sa.ForeignKeyConstraint(["source_warehouse_id"], ["warehouse_warehouses.id"]),
            sa.ForeignKeyConstraint(["source_location_id"], ["warehouse_locations.id"]),
            sa.ForeignKeyConstraint(["source_project_id"], ["warehouse_projects.id"]),
            sa.ForeignKeyConstraint(["target_warehouse_id"], ["warehouse_warehouses.id"]),
            sa.ForeignKeyConstraint(["target_location_id"], ["warehouse_locations.id"]),
            sa.ForeignKeyConstraint(["target_project_id"], ["warehouse_projects.id"]),
            sa.ForeignKeyConstraint(["original_document_line_id"], ["warehouse_document_lines.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("document_id", "line_no", name="uq_warehouse_document_line_no"),
        )
        op.create_index("ix_warehouse_document_lines_document_id", "warehouse_document_lines", ["document_id"])
        op.create_index("ix_warehouse_document_lines_material_id", "warehouse_document_lines", ["material_id"])

    if "warehouse_ledger_entries" not in existing_tables:
        op.create_table(
            "warehouse_ledger_entries",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("document_line_id", sa.Integer(), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("location_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.Integer(), nullable=False),
            sa.Column("quantity_delta", sa.Numeric(18, 4), nullable=False),
            sa.Column("occurred_on", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["document_id"], ["warehouse_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["document_line_id"], ["warehouse_document_lines.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse_warehouses.id"]),
            sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"]),
            sa.ForeignKeyConstraint(["project_id"], ["warehouse_projects.id"]),
            sa.ForeignKeyConstraint(["material_id"], ["warehouse_materials.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "document_line_id",
                "warehouse_id",
                "location_id",
                "project_id",
                "material_id",
                name="uq_warehouse_ledger_line_dimension",
            ),
        )
        op.create_index("ix_warehouse_ledger_warehouse_id", "warehouse_ledger_entries", ["warehouse_id"])
        op.create_index("ix_warehouse_ledger_material_id", "warehouse_ledger_entries", ["material_id"])
        op.create_index("ix_warehouse_ledger_occurred_on", "warehouse_ledger_entries", ["occurred_on"])

    if "warehouse_stock_balances" not in existing_tables:
        op.create_table(
            "warehouse_stock_balances",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("location_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.CheckConstraint("quantity >= 0", name="ck_warehouse_stock_non_negative"),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse_warehouses.id"]),
            sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"]),
            sa.ForeignKeyConstraint(["project_id"], ["warehouse_projects.id"]),
            sa.ForeignKeyConstraint(["material_id"], ["warehouse_materials.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "warehouse_id",
                "location_id",
                "project_id",
                "material_id",
                name="uq_warehouse_stock_dimension",
            ),
        )
        op.create_index("ix_warehouse_stock_warehouse_id", "warehouse_stock_balances", ["warehouse_id"])
        op.create_index("ix_warehouse_stock_material_id", "warehouse_stock_balances", ["material_id"])

    if "warehouse_counts" not in existing_tables:
        op.create_table(
            "warehouse_counts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("count_no", sa.String(length=40), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("location_id", sa.Integer(), nullable=True),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("counted_on", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="DRAFT"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("confirmed_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("adjustment_document_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse_warehouses.id"]),
            sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"]),
            sa.ForeignKeyConstraint(["project_id"], ["warehouse_projects.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["adjustment_document_id"], ["warehouse_documents.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("count_no"),
        )
        op.create_index("ix_warehouse_counts_warehouse_id", "warehouse_counts", ["warehouse_id"])

    if "warehouse_count_lines" not in existing_tables:
        op.create_table(
            "warehouse_count_lines",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("count_id", sa.Integer(), nullable=False),
            sa.Column("warehouse_id", sa.Integer(), nullable=False),
            sa.Column("location_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.Integer(), nullable=False),
            sa.Column("book_quantity", sa.Numeric(18, 4), nullable=False),
            sa.Column("counted_quantity", sa.Numeric(18, 4), nullable=True),
            sa.Column("adjustment_document_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["count_id"], ["warehouse_counts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse_warehouses.id"]),
            sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"]),
            sa.ForeignKeyConstraint(["project_id"], ["warehouse_projects.id"]),
            sa.ForeignKeyConstraint(["material_id"], ["warehouse_materials.id"]),
            sa.ForeignKeyConstraint(["adjustment_document_id"], ["warehouse_documents.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "count_id",
                "warehouse_id",
                "location_id",
                "project_id",
                "material_id",
                name="uq_warehouse_count_line_dimension",
            ),
        )
        op.create_index("ix_warehouse_count_lines_count_id", "warehouse_count_lines", ["count_id"])

    if "warehouse_business_supplements" not in existing_tables:
        op.create_table(
            "warehouse_business_supplements",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("document_line_id", sa.Integer(), nullable=True),
            sa.Column("delivery_note_no", sa.String(length=100), nullable=True),
            sa.Column("acceptance_no", sa.String(length=100), nullable=True),
            sa.Column("contract_no", sa.String(length=100), nullable=True),
            sa.Column("manufacturer", sa.String(length=200), nullable=True),
            sa.Column("price_type", sa.String(length=50), nullable=True),
            sa.Column("unit_price", sa.Numeric(18, 4), nullable=True),
            sa.Column("amount", sa.Numeric(18, 2), nullable=True),
            sa.Column("weigh_in", sa.Numeric(18, 4), nullable=True),
            sa.Column("residual_value", sa.Numeric(18, 2), nullable=True),
            sa.Column("admin_notes", sa.Text(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["document_id"], ["warehouse_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["document_line_id"], ["warehouse_document_lines.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_warehouse_business_supplements_document_id",
            "warehouse_business_supplements",
            ["document_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())
    for table in WAREHOUSE_TABLES:
        if table in existing_tables:
            op.drop_table(table)
