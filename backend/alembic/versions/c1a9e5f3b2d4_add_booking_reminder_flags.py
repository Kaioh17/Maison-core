"""add booking reminder flags

Revision ID: c1a9e5f3b2d4
Revises: b7f2c14a9d30
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a9e5f3b2d4'
down_revision: Union[str, Sequence[str], None] = 'b7f2c14a9d30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('reminder_24h_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('bookings', sa.Column('reminder_1h_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('bookings', sa.Column('confirm_reminder_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bookings', 'confirm_reminder_sent')
    op.drop_column('bookings', 'reminder_1h_sent')
    op.drop_column('bookings', 'reminder_24h_sent')
