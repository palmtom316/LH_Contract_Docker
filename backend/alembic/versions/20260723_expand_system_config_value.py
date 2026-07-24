"""Allow encrypted integration credentials in system configuration."""

from alembic import op
import sqlalchemy as sa


revision = "20260723_expand_system_config"
down_revision = "20260723_zero_hour_finance_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sys_config",
        "value",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade():
    bind = op.get_bind()
    longest_value = bind.execute(
        sa.text("SELECT COALESCE(MAX(length(value)), 0) FROM sys_config")
    ).scalar_one()
    if longest_value > 500:
        raise RuntimeError(
            "Cannot restore sys_config.value VARCHAR(500): existing value exceeds 500 characters"
        )
    op.alter_column(
        "sys_config",
        "value",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
