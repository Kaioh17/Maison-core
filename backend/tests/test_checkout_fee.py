"""Platform fee and cents conversion on the rider checkout PaymentIntent.

The fee used to be computed on whole dollars (a $150.75 fare paid fee on $150) and dollars were
converted with int(price * 100), which turns 19.99 into 1998.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.api.services.stripe_services.checkout import BookingCheckout


@pytest.fixture(autouse=True)
def cleanup_db():
    """No-op override of the conftest autouse DB cleanup -- no DB here."""
    yield


@pytest.fixture
def checkout():
    c = BookingCheckout.__new__(BookingCheckout)
    c.role, c.tenant_id, c.sub_plan = "rider", 1, "free"  # free plan: 3 percent
    c._is_deposit = lambda booking_obj: False
    return c


@pytest.mark.parametrize("dollars,cents", [(19.99, 1999), (150.75, 15075), (0.29, 29), (1.005, 101), (200, 20000)])
def test_to_cent_is_exact(checkout, dollars, cents):
    assert checkout._to_cent(dollars) == cents


@pytest.mark.parametrize("cents,rate,fee", [(15075, 0.03, 452), (10000, 0.03, 300), (1999, 0.01, 20), (50, 0.03, 2)])
def test_fee_is_on_the_exact_amount_rounded_half_up(checkout, cents, rate, fee):
    assert checkout._fee_cents(cents, rate) == fee


def test_payment_intent_carries_the_exact_amount_and_fee(checkout):
    booking = SimpleNamespace(
        id=7, rider_id=3, tenant_id=1, estimated_price=150.75, service_type="dropoff", payment_status="pending",
        payment_id=None, tenant=SimpleNamespace(profile=SimpleNamespace(charges_enabled=True, stripe_account_id="acct_1")),
        rider=SimpleNamespace(stripe_customer_id="cus_1", email="r@x.co"),
    )
    with patch("stripe.PaymentIntent.create", return_value=SimpleNamespace(id="pi_1", metadata={})) as create, \
         patch("stripe.PaymentIntent.retrieve", return_value=SimpleNamespace(client_secret="sec")):
        asyncio.run(checkout.checkout_session(booking))
    kwargs = create.call_args.kwargs
    assert kwargs["amount"] == 15075
    assert kwargs["application_fee_amount"] == 452  # was 450: 3 percent of $150, not of $150.75
