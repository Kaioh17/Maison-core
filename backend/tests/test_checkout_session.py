"""Guards the two Stripe Checkout kwargs the founding-operator offer depends on.

`allow_promotion_codes` is what makes the discount enterable at all, and
`payment_method_collection='always'` is what stops a deep discount from turning
a design partner into a free pilot with no card on file. Both are easy to drop
in a refactor and neither fails loudly -- checkout keeps working, the commercial
terms just quietly stop holding.
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
def service():
    tenant = SimpleNamespace(
        id=1, slug="acme", role="tenant", subscription_plan="growth"
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        stripe_customer_id="cus_test", stripe_account_id="acct_test"
    )
    return StripeService(current_user=tenant, db=db)


def test_checkout_session_allows_promo_codes_and_always_collects_a_card(service):
    with patch(
             "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
             return_value="growth",
         ), \
         patch(
             "stripe.checkout.Session.create",
             return_value=SimpleNamespace(
                 url="https://checkout.stripe.test/s", customer="cus_test",
                 amount_subtotal=29999,
             ),
         ) as create:
        asyncio.run(service.create_checkout_session("price_growth", "growth"))

    kwargs = create.call_args.kwargs
    assert kwargs["allow_promotion_codes"] is True
    # Lowercase spelling matters: Stripe rejects unknown params, and the generic
    # `except Exception` in create_checkout_session would mask it as a 502.
    assert kwargs["payment_method_collection"] == "always"
