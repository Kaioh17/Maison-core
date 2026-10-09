"""drivers.nav_app and bookings.driver_started_at / driver_arrived_at

Revision ID: a7e1c4d9b2f6
Revises: f6c8d3e0b4a7
Create Date: 2026-10-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7e1c4d9b2f6'
down_revision: Union[str, Sequence[str], None] = 'f6c8d3e0b4a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _missing(table: str, column: str) -> bool:
    return column not in [c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)]


def upgrade() -> None:
    if _missing('drivers', 'nav_app'):
        op.add_column('drivers', sa.Column('nav_app', sa.String(16), nullable=True))
        op.create_check_constraint('check_driver_nav_app', 'drivers', "nav_app IS NULL OR nav_app IN ('google', 'apple', 'waze')")
    for col in ('driver_started_at', 'driver_arrived_at'):
        if _missing('bookings', col):
            op.add_column('bookings', sa.Column(col, sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('bookings', 'driver_arrived_at')
    op.drop_column('bookings', 'driver_started_at')
    op.drop_constraint('check_driver_nav_app', 'drivers', type_='check')
    op.drop_column('drivers', 'nav_app')
