"""tenants without a subscription id are 'unsubscribed', not 'free'

Revision ID: d4e8a1c7f5b2
Revises: c1a9e5f3b2d4
Create Date: 2026-10-01 00:00:00.000000

Free is a real $0 Stripe subscription, so a tenant with no cur_subscription_id
is on no plan at all and cannot be upgraded later (there is nothing to modify).
Until now they were stored as plan 'free' / status 'inactive', which read as a
valid free account. They become plan NULL / status 'unsubscribed' so the app
can tell them apart and prompt them to subscribe.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8a1c7f5b2'
down_revision: Union[str, Sequence[str], None] = 'c1a9e5f3b2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE tenants_profile SET subscription_status = 'unsubscribed', "
            "subscription_plan = NULL WHERE cur_subscription_id IS NULL"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE tenants_profile SET subscription_status = 'inactive', "
            "subscription_plan = 'free' WHERE subscription_status = 'unsubscribed'"
        )
    )
