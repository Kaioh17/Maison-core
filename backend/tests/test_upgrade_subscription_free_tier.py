"""Guards the free-tier crash: a tenant who has never subscribed has
`cur_subscription_id = None` (free is "no subscription", never a real Stripe
one -- see domain/billing.py). `Subscription.retrieve(None)` blows up with
`InvalidRequestError`. Upgrading off free must start a Checkout session
instead of trying to modify a subscription that doesn't exist.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.api.services.stripe_services.stripe_tier_service import StripeService


@pytest.fixture(autouse=True)
def cleanup_db():
    """No-op override of the conftest autouse DB cleanup -- no DB here."""
    yield


@pytest.fixture
def free_tier_service():
    tenant = SimpleNamespace(id=1, slug="acme", role="tenant", subscription_plan="free")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        stripe_customer_id="cus_test", cur_subscription_id=None, stripe_account_id=None
    )
    return StripeService(current_user=tenant, db=db)


def test_free_tier_upgrade_starts_checkout_not_modify(free_tier_service):
    with patch(
        "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
        return_value="growth",
    ), patch("stripe.Subscription.retrieve") as retrieve, patch(
        "stripe.checkout.Session.create",
        return_value=SimpleNamespace(
            url="https://checkout.stripe.com/x", customer="cus_test", amount_subtotal=29999
        ),
    ) as create:
        result = asyncio.run(free_tier_service.upgrade_subscription("price_growth", "growth"))

    retrieve.assert_not_called()
    create.assert_called_once()
    assert result.data["product_type"] == "growth"
