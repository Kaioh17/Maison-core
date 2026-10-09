"""pilot program: legal_acceptances consent log and tenants.pilot_ends_at

Revision ID: f6c8d3e0b4a7
Revises: e5b7c2d9a1f3
Create Date: 2026-10-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6c8d3e0b4a7'
down_revision: Union[str, Sequence[str], None] = 'e5b7c2d9a1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # main.py runs Base.metadata.create_all at startup, which may have created the table already.
    insp = sa.inspect(op.get_bind())
    if 'pilot_ends_at' not in [c['name'] for c in insp.get_columns('tenants')]:
        op.add_column('tenants', sa.Column('pilot_ends_at', sa.TIMESTAMP(timezone=True), nullable=True))
    if insp.has_table('legal_acceptances'):
        return
    op.create_table(
        'legal_acceptances',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(40), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('ip_address', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.String(400), nullable=True),
        sa.Column('accepted_on', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('tenant_id', 'version', name='uq_legal_tenant_version'),
    )
    op.create_index('ix_legal_acceptances_tenant_id', 'legal_acceptances', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_legal_acceptances_tenant_id', table_name='legal_acceptances')
    op.drop_table('legal_acceptances')
    op.drop_column('tenants', 'pilot_ends_at')
