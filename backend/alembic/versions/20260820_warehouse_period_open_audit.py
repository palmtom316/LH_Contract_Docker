"""Record explicit warehouse period opening approvals."""

from alembic import op
import sqlalchemy as sa


revision = "20260820_warehouse_period_open_audit"
down_revision = "20260819_warehouse_p1_trace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {
        column["name"] for column in inspector.get_columns("warehouse_periods")
    }
    columns = (
        sa.Column("opened_by", sa.Integer(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("open_reason", sa.Text(), nullable=True),
    )
    for column in columns:
        if column.name not in existing:
            op.add_column("warehouse_periods", column)
    foreign_keys = {
        foreign_key["name"]
        for foreign_key in sa.inspect(bind).get_foreign_keys("warehouse_periods")
    }
    if "fk_warehouse_periods_opened_by" not in foreign_keys:
        op.create_foreign_key(
            "fk_warehouse_periods_opened_by", "warehouse_periods", "users", ["opened_by"], ["id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    foreign_keys = {
        foreign_key["name"]
        for foreign_key in sa.inspect(bind).get_foreign_keys("warehouse_periods")
    }
    if "fk_warehouse_periods_opened_by" in foreign_keys:
        op.drop_constraint("fk_warehouse_periods_opened_by", "warehouse_periods", type_="foreignkey")
    existing = {
        column["name"] for column in sa.inspect(bind).get_columns("warehouse_periods")
    }
    for name in ("open_reason", "opened_at", "opened_by"):
        if name in existing:
            op.drop_column("warehouse_periods", name)
