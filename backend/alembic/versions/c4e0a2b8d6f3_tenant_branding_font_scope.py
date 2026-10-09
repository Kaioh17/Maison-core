"""tenant_branding font_scope

Revision ID: c4e0a2b8d6f3
Revises: b3d9f1a7c5e2
Create Date: 2026-10-09 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4e0a2b8d6f3'
down_revision: Union[str, Sequence[str], None] = 'b3d9f1a7c5e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('tenant_branding')}
    if 'font_scope' not in existing:
        op.add_column('tenant_branding', sa.Column('font_scope', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('tenant_branding', 'font_scope')
