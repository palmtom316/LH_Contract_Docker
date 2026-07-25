"""Store refresh-token timestamps as timezone-aware UTC values."""

from alembic import op
import sqlalchemy as sa


revision = "20260725_refresh_token_timestamps_utc"
down_revision = "20260725_remove_bank_receipts"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    op.alter_column(
        "refresh_tokens",
        "created_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "refresh_tokens",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        existing_nullable=True,
    )
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
