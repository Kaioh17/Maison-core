"""Unsubscribed tenants are never entitled; billing parsing copes with both Stripe discount shapes."""
from app.domain.plans import SubStatus, is_entitled, resolve_status
from app.api.services.stripe_services.stripe_tier_service import StripeService


def test_unsubscribed_is_its_own_status_and_not_entitled():
    assert resolve_status("unsubscribed") == SubStatus.UNSUBSCRIBED.value
    assert not is_entitled("unsubscribed")
    assert not is_entitled(None)  # missing falls back to inactive, still not entitled
    assert is_entitled("active")


def test_discount_summary_reads_coupon_on_basil_and_under_source_on_later_api_versions():
    coupon = {"name": "founding-operator", "percent_off": 100.0, "duration": "forever"}
    for discount in ({"coupon": coupon}, {"source": {"coupon": coupon}}):
        out = StripeService._discount_summary({"discounts": [discount]})
        assert out["name"] == "founding-operator" and out["percent_off"] == 100.0 and out["duration"] == "forever"


def test_discount_summary_ignores_missing_and_unexpanded_discounts():
    assert StripeService._discount_summary({"discounts": []}) is None
    assert StripeService._discount_summary({"discounts": ["di_123"]}) is None


def test_card_summary_uses_the_subscription_default_payment_method():
    sub = {"default_payment_method": {"card": {"brand": "visa", "last4": "0077", "exp_month": 9, "exp_year": 2029}}}
    assert StripeService._card_summary(sub, profile=None) == {"brand": "visa", "last4": "0077", "exp_month": 9, "exp_year": 2029}
