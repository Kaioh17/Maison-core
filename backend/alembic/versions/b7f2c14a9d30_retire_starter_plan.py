"""retire starter plan: map subscription_plan 'starter' -> 'free'

Revision ID: b7f2c14a9d30
Revises: 9c3d6de90692
Create Date: 2026-07-18 00:00:00.000000

The starter tier is gone from PLAN_REGISTRY. resolve_plan() already falls back
to FREE_PLAN for any unrecognised value, so a leftover 'starter' row is not a
crash -- but it is a lie in the database: the tenant's stored plan would no
longer match anything the API can name back to them, and every report that
groups by subscription_plan would carry a phantom tier forever. This rewrites
them once so the column only ever holds a live plan name.

Starter and free had identical quotas (1 vehicle, 1 driver), so no tenant loses
capacity here. What does change is the take rate: free is now 3% where starter
was 2%. That is intentional -- see maison_frontend/PRICING_RATIONALE.md.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f2c14a9d30'
down_revision: Union[str, Sequence[str], None] = '9c3d6de90692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Collapse starter into free."""
    op.execute(
        sa.text(
            "UPDATE tenants_profile SET subscription_plan = 'free' "
            "WHERE lower(trim(subscription_plan)) = 'starter'"
        )
    )


def downgrade() -> None:
    """Irreversible by design.

    Starter and free are indistinguishable in the data once merged -- a tenant
    who signed up on free and one who was migrated off starter both read 'free'.
    Guessing which rows to send back would invent history, so this is a no-op:
    downgrading the schema leaves every tenant on free, which is a valid plan.
    """
    pass
