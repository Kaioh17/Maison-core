"""Guards the founding-operator coupon scope (directives.md founding-terms-2026-08):
it must not carry over when a tenant upgrades to a higher-priced tier.

A tier change is confirmed in Stripe's Billing Portal (directives.md
billing-confirm-2026-08), but the portal's own
`flow_data.subscription_update_confirm.discounts` field only *applies* a
coupon -- it has no clear/remove semantics, and `Subscription.modify` with
`discounts=[]` (an empty *array*) is documented by Stripe to leave discounts
unchanged, not clear them. Both were tried and both no-op, which is how a
Fleet upgrade billed $0.00 in real test-mode verification. The only
documented way to actually strip a discount is `Subscription.modify(...,
discounts="")` (an empty *string*), called directly on the subscription
before the portal session is created.
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
    tenant = SimpleNamespace(id=1, slug="acme", role="tenant", subscription_plan="growth")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        stripe_customer_id="cus_test", cur_subscription_id="sub_test"
    )
    return StripeService(current_user=tenant, db=db)


class _StripeObj(dict):
    """Minimal stand-in for Stripe's dual dict/attribute-access objects --
    the real code reads `.id` in one place and `['price']['id']` in another."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


def _subscription(price_id, discounted):
    sub = _StripeObj(
        items={"data": [_StripeObj(id="si_test", price=_StripeObj(id=price_id))]},
    )
    if discounted:
        sub["discount"] = {"coupon": {"id": "founding-operator"}}
    return sub


def test_price_change_strips_the_discount(service):
    with patch(
        "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
        return_value="fleet",
    ), patch(
        "stripe.Subscription.retrieve",
        return_value=_subscription("price_growth", discounted=True),
    ), patch(
        "stripe.Subscription.modify"
    ) as modify, patch(
        "stripe.billing_portal.Session.create",
        return_value=SimpleNamespace(url="https://billing.stripe.com/p/session_test"),
    ):
        asyncio.run(service.upgrade_subscription("price_fleet", "fleet"))

    modify.assert_called_once_with("sub_test", discounts="")


def test_same_price_leaves_discount_alone(service):
    """Re-saving the current tier (e.g. metadata refresh) must not touch billing."""
    with patch(
        "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
        return_value="growth",
    ), patch(
        "stripe.Subscription.retrieve",
        return_value=_subscription("price_growth", discounted=True),
    ), patch(
        "stripe.Subscription.modify"
    ) as modify, patch(
        "stripe.billing_portal.Session.create",
        return_value=SimpleNamespace(url="https://billing.stripe.com/p/session_test"),
    ):
        asyncio.run(service.upgrade_subscription("price_growth", "growth"))

    modify.assert_not_called()


def test_no_existing_discount_skips_the_strip_call(service):
    """No coupon on the subscription -- nothing to strip, don't call modify."""
    with patch(
        "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
        return_value="fleet",
    ), patch(
        "stripe.Subscription.retrieve",
        return_value=_subscription("price_growth", discounted=False),
    ), patch(
        "stripe.Subscription.modify"
    ) as modify, patch(
        "stripe.billing_portal.Session.create",
        return_value=SimpleNamespace(url="https://billing.stripe.com/p/session_test"),
    ):
        asyncio.run(service.upgrade_subscription("price_fleet", "fleet"))

    modify.assert_not_called()
