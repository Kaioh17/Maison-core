"""Guards the founding-operator coupon scope (directives.md founding-terms-2026-08):
it must not carry over when a tenant upgrades to a higher-priced tier. Stripe
discounts attach to the subscription, not the price, so `Subscription.modify`
silently keeps a 100%-off coupon applied to the new price unless we strip it.
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
        "stripe.Subscription.modify",
        return_value=SimpleNamespace(id="sub_test", customer="cus_test", status="active"),
    ) as modify:
        asyncio.run(service.upgrade_subscription("price_fleet", "fleet"))

    assert modify.call_args.kwargs["discounts"] == []


def test_same_price_leaves_discount_alone(service):
    """Re-saving the current tier (e.g. metadata refresh) must not touch billing."""
    with patch(
        "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
        return_value="growth",
    ), patch(
        "stripe.Subscription.retrieve",
        return_value=_subscription("price_growth", discounted=True),
    ), patch(
        "stripe.Subscription.modify",
        return_value=SimpleNamespace(id="sub_test", customer="cus_test", status="active"),
    ) as modify:
        asyncio.run(service.upgrade_subscription("price_growth", "growth"))

    assert "discounts" not in modify.call_args.kwargs


def test_no_existing_discount_omits_the_param(service):
    """No coupon on the subscription -- nothing to strip, don't send the param."""
    with patch(
        "app.api.services.stripe_services.stripe_tier_service.price_to_plan",
        return_value="fleet",
    ), patch(
        "stripe.Subscription.retrieve",
        return_value=_subscription("price_growth", discounted=False),
    ), patch(
        "stripe.Subscription.modify",
        return_value=SimpleNamespace(id="sub_test", customer="cus_test", status="active"),
    ) as modify:
        asyncio.run(service.upgrade_subscription("price_fleet", "fleet"))

    assert "discounts" not in modify.call_args.kwargs
