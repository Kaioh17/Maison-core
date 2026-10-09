"""tenant_branding font_heading, font_body, font_accent

Revision ID: b3d9f1a7c5e2
Revises: a7e1c4d9b2f6
Create Date: 2026-10-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3d9f1a7c5e2'
down_revision: Union[str, Sequence[str], None] = 'a7e1c4d9b2f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = ('font_heading', 'font_body', 'font_accent')


def upgrade() -> None:
    # main.py runs Base.metadata.create_all at startup; it never alters existing tables, but be safe on re-runs.
    existing = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('tenant_branding')}
    for name in COLUMNS:
        if name not in existing:
            op.add_column('tenant_branding', sa.Column(name, sa.String(), nullable=True))


def downgrade() -> None:
    for name in COLUMNS:
        op.drop_column('tenant_branding', name)
