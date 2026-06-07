"""Add downstream_upstream_allocations table

Revision ID: 20260526_add_downstream_allocations
Revises: 20260203_add_refresh_tokens
Create Date: 2026-05-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260526_add_downstream_allocations"
down_revision = "20260203_add_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if "downstream_upstream_allocations" not in table_names:
        op.create_table(
            "downstream_upstream_allocations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "downstream_contract_id",
                sa.Integer(),
                sa.ForeignKey(
                    "contracts_downstream.id",
                    ondelete="CASCADE",
                    onupdate="CASCADE",
                ),
                nullable=False,
            ),
            sa.Column(
                "upstream_contract_id",
                sa.Integer(),
                sa.ForeignKey(
                    "contracts_upstream.id",
                    ondelete="RESTRICT",
                    onupdate="CASCADE",
                ),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("description", sa.String(length=300), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.UniqueConstraint(
                "downstream_contract_id",
                "upstream_contract_id",
                name="uq_downstream_upstream_allocation",
            ),
        )

    existing_indexes = {
        idx["name"] for idx in sa.inspect(conn).get_indexes("downstream_upstream_allocations")
    }
    if op.f("ix_downstream_upstream_allocations_downstream_contract_id") not in existing_indexes:
        op.create_index(
            op.f("ix_downstream_upstream_allocations_downstream_contract_id"),
            "downstream_upstream_allocations",
            ["downstream_contract_id"],
            unique=False,
        )
    if op.f("ix_downstream_upstream_allocations_upstream_contract_id") not in existing_indexes:
        op.create_index(
            op.f("ix_downstream_upstream_allocations_upstream_contract_id"),
            "downstream_upstream_allocations",
            ["upstream_contract_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_downstream_upstream_allocations_upstream_contract_id"),
        table_name="downstream_upstream_allocations",
    )
    op.drop_index(
        op.f("ix_downstream_upstream_allocations_downstream_contract_id"),
        table_name="downstream_upstream_allocations",
    )
    op.drop_table("downstream_upstream_allocations")
