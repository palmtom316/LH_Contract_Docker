"""Add dedicated ignored lifecycle audit fields to bank receipts."""
from alembic import op
import sqlalchemy as sa

revision = "20260722_receipt_ignore"
down_revision = "20260721_bank_receipts"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("bank_receipt_items")}
    if "ignored_reason" not in columns:
        op.add_column("bank_receipt_items", sa.Column("ignored_reason", sa.String(300)))
    if "ignored_by" not in columns:
        op.add_column("bank_receipt_items", sa.Column("ignored_by", sa.Integer(), sa.ForeignKey("users.id")))
    if "ignored_at" not in columns:
        op.add_column("bank_receipt_items", sa.Column("ignored_at", sa.DateTime(timezone=True)))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("bank_receipt_items")}
    for name in ("ignored_at", "ignored_by", "ignored_reason"):
        if name in columns:
            op.drop_column("bank_receipt_items", name)
