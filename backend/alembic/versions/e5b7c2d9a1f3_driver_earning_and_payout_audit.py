"""bookings.driver_earning and payout audit columns

Revision ID: e5b7c2d9a1f3
Revises: d4e8a1c7f5b2
Create Date: 2026-10-01 00:00:00.000000

driver_earning is the frozen per-ride driver pay (source of truth, never recomputed).
payouts gets an adjustment, an audit trail (who/when/note), one row per booking, and a status check.
payouts was never written to before this, so the constraints cannot conflict with existing rows.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5b7c2d9a1f3'
down_revision: Union[str, Sequence[str], None] = 'd4e8a1c7f5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bookings', sa.Column('driver_earning', sa.Float(), nullable=True))
    op.add_column('payouts', sa.Column('adjustment', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('payouts', sa.Column('status_by_role', sa.String(20), nullable=True))
    op.add_column('payouts', sa.Column('status_by_id', sa.Integer(), nullable=True))
    op.add_column('payouts', sa.Column('status_on', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('payouts', sa.Column('note', sa.String(), nullable=True))
    op.create_unique_constraint('uq_payout_booking', 'payouts', ['booking_id'])
    op.create_check_constraint(
        'payout_status_check', 'payouts', "status IN ('pending', 'paid', 'disputed', 'verified')"
    )


def downgrade() -> None:
    op.drop_constraint('payout_status_check', 'payouts', type_='check')
    op.drop_constraint('uq_payout_booking', 'payouts', type_='unique')
    for col in ('note', 'status_on', 'status_by_id', 'status_by_role', 'adjustment'):
        op.drop_column('payouts', col)
    op.drop_column('bookings', 'driver_earning')
