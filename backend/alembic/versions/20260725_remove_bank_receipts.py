"""Remove bank receipt recognition module and MinerU configuration."""

from alembic import op
import sqlalchemy as sa


revision = "20260725_remove_bank_receipts"
down_revision = "20260723_expand_system_config"
branch_labels = None
depends_on = None


RECEIPT_SOURCE_TABLES = (
    "finance_upstream_receipts",
    "finance_downstream_payments",
    "finance_management_payments",
    "finance_zero_hour_payments",
)

RECEIPT_SOURCE_COLUMNS = (
    "source_bank_receipt_item_id",
    "source_bank_receipt_allocation_id",
    "bank_serial_number",
    "transaction_at",
)

MINERU_CONFIG_KEYS = (
    "mineru_api_url",
    "mineru_api_key",
    "mineru_enabled",
    "mineru_timeout_seconds",
    "company_bank_accounts",
)


def _drop_column_if_exists(inspector, table: str, column: str) -> None:
    if table not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns(table)}
    if column not in columns:
        return
    # Drop dependent indexes first when present.
    for index in inspector.get_indexes(table):
        if column in (index.get("column_names") or []):
            op.drop_index(index["name"], table_name=table)
    for fk in inspector.get_foreign_keys(table):
        if column in (fk.get("constrained_columns") or []):
            if fk.get("name"):
                op.drop_constraint(fk["name"], table, type_="foreignkey")
    for uq in inspector.get_unique_constraints(table):
        if column in (uq.get("column_names") or []):
            if uq.get("name"):
                op.drop_constraint(uq["name"], table, type_="unique")
    op.drop_column(table, column)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in RECEIPT_SOURCE_TABLES:
        for column in RECEIPT_SOURCE_COLUMNS:
            _drop_column_if_exists(inspector, table, column)
            inspector = sa.inspect(bind)

    for table in (
        "bank_receipt_match_candidates",
        "bank_receipt_allocations",
        "bank_receipt_items",
        "bank_receipt_batches",
    ):
        if table in inspector.get_table_names():
            op.drop_table(table)
            inspector = sa.inspect(bind)

    if "sys_config" in inspector.get_table_names():
        keys_sql = ", ".join(f"'{key}'" for key in MINERU_CONFIG_KEYS)
        op.execute(sa.text(f"DELETE FROM sys_config WHERE key IN ({keys_sql})"))


def downgrade():
    # Bank receipt recognition was removed intentionally; re-create from prior
    # migrations if a full rollback is required.
    raise NotImplementedError("Bank receipt module removal is not reversible")
