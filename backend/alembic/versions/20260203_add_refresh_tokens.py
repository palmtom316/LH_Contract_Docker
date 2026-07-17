"""Add refresh_tokens table

Revision ID: 20260203_add_refresh_tokens
Revises: 20260122_add_optimized_indexes
Create Date: 2026-02-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260203_add_refresh_tokens"
down_revision = "20260122_add_optimized_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if "refresh_tokens" not in table_names:
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("jti", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now())
        )

    existing_indexes = {
        idx["name"] for idx in sa.inspect(conn).get_indexes("refresh_tokens")
    }
    if op.f("ix_refresh_tokens_jti") not in existing_indexes:
        op.create_index(op.f("ix_refresh_tokens_jti"), "refresh_tokens", ["jti"], unique=True)
    if op.f("ix_refresh_tokens_user_id") not in existing_indexes:
        op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_jti"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
