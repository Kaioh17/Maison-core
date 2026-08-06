"""Unit tests for the plan/subscription policy layer.

Deliberately free of DB fixtures: these guard the pure decision logic that
every quota-consuming path now routes through.
"""
import json

import pytest
from fastapi import HTTPException

from app.domain.plans import (
    FLEET_PLAN,
    FREE_PLAN,
    GROWTH_PLAN,
    PLAN_LADDER,
    PLAN_REGISTRY,
    PlanName,
    SubStatus,
    is_entitled,
    resolve_plan,
    resolve_status,
)
from app.policies.plan_policy import PlanPolicy, PlanPolicyError, _exceeds


@pytest.fixture(autouse=True)
def cleanup_db():
    """No-op override of the conftest autouse DB cleanup.

    These are pure unit tests -- they touch no database, and the shared
    fixture's teardown currently errors, which would mask real results.
    """
    yield


class TestResolvePlan:
    @pytest.mark.parametrize("value", [None, "", "free", "bogus", "FREE", 0])
    def test_falls_back_to_free_never_raises(self, value):
        # subscription_plan defaults to "free" in the DB, which has no paid
        # tier; a raising lookup used to 500 every never-subscribed tenant.
        assert resolve_plan(value) is FREE_PLAN

    @pytest.mark.parametrize(
        "value,expected",
        [("free", FREE_PLAN), ("growth", GROWTH_PLAN), ("fleet", FLEET_PLAN)],
    )
    def test_resolves_known_tiers(self, value, expected):
        assert resolve_plan(value) is expected

    def test_is_case_and_whitespace_insensitive(self):
        assert resolve_plan("  FLEET ") is FLEET_PLAN

    def test_retired_starter_resolves_to_free(self):
        # The b7f2c14a9d30 migration rewrites stored 'starter' rows to 'free',
        # but a row written by an older instance mid-deploy must not 500 --
        # the unrecognised-value fallback is what covers that window.
        assert resolve_plan("starter") is FREE_PLAN
        assert "starter" not in PLAN_REGISTRY


class TestTierLadder:
    def test_registry_is_exactly_three_tiers(self):
        assert set(PLAN_REGISTRY) == {"free", "growth", "fleet"}

    def test_plan_name_enum_matches_registry(self):
        # The enum and the registry are two lists of the same thing; a tier
        # removed from one and left in the other is how `starter` lingered.
        assert {p.value for p in PlanName} == set(PLAN_REGISTRY)

    def test_price_rises_as_tier_rises(self):
        # The ladder must be monotonic in price as well as in limits, or the
        # "upgrade" framing on the pricing page is a lie.
        prices = [p.monthly_price_cents for p in PLAN_LADDER]
        assert prices == sorted(prices)
        assert FREE_PLAN.monthly_price_cents == 0

    def test_prices_are_whole_cents(self):
        # These are serialized straight into the pricing UI. A float here would
        # render as "$299.99000000000001".
        for p in PLAN_LADDER:
            assert isinstance(p.monthly_price_cents, int)

    def test_only_free_is_unpriced(self):
        # A zero price means "not purchasable" to the frontend, which routes
        # those tiers past checkout. Exactly one tier may claim it.
        unpriced = [p.name for p in PLAN_LADDER if p.monthly_price_cents == 0]
        assert unpriced == ["free"]

    def test_take_rate_declines_as_tier_rises(self):
        # The whole point of the ladder: a paid tier buys a smaller cut of your
        # own revenue. If this ever inverts, upgrading costs money twice.
        assert FREE_PLAN.maison_fee == 0.03
        assert GROWTH_PLAN.maison_fee == 0.02
        assert FLEET_PLAN.maison_fee == 0.01
        assert FREE_PLAN.maison_fee > GROWTH_PLAN.maison_fee > FLEET_PLAN.maison_fee


class TestLimits:
    def test_growth_is_five_vehicles_seven_drivers(self):
        # These were swapped relative to what customers were sold.
        assert GROWTH_PLAN.max_vehicle == 5
        assert GROWTH_PLAN.max_driver_count == 7

    def test_fleet_is_unlimited(self):
        assert FLEET_PLAN.max_vehicle is None
        assert FLEET_PLAN.max_driver_count is None

    def test_unlimited_serializes_as_null_not_infinity(self):
        # The limits endpoint returns these. math.inf would emit the bare token
        # `Infinity`, which is invalid JSON and throws in the browser.
        payload = json.dumps(FLEET_PLAN.to_dict())
        assert '"max_vehicle": null' in payload
        assert "Infinity" not in payload

    def test_every_registry_entry_is_serializable(self):
        json.dumps({name: p.to_dict() for name, p in PLAN_REGISTRY.items()})


class TestExceeds:
    def test_none_limit_is_unlimited(self):
        assert _exceeds(999_999, None) is False

    def test_blocks_at_the_limit_not_past_it(self):
        assert _exceeds(0, 1) is False
        assert _exceeds(1, 1) is True

    def test_over_limit_tenant_stays_blocked(self):
        # A fleet tenant with 30 vehicles who downgrades to free keeps their
        # rows but can create nothing until they delete down.
        assert _exceeds(30, 1) is True


class TestStatus:
    @pytest.mark.parametrize("status", ["active", "trialing", "past_due"])
    def test_entitled_statuses(self, status):
        # past_due is entitled on purpose: a failed card gets a grace period
        # rather than instantly halting the tenant's operations.
        assert is_entitled(status) is True

    @pytest.mark.parametrize(
        "status", ["canceled", "unpaid", "incomplete", "inactive", None, "", "nonsense"]
    )
    def test_unentitled_statuses(self, status):
        assert is_entitled(status) is False

    def test_unknown_status_normalizes_to_inactive(self):
        assert resolve_status("nonsense") == SubStatus.INACTIVE.value
        assert resolve_status(None) == SubStatus.INACTIVE.value

    def test_stripe_statuses_round_trip(self):
        assert resolve_status("PAST_DUE") == "past_due"


class TestPlanPolicy:
    def test_quota_rejection_is_402_with_detail(self):
        # 401 would trigger a token-refresh loop in the client; 403 renders as
        # a generic "access denied". 402 is the only usable billing signal.
        with pytest.raises(PlanPolicyError) as exc:
            PlanPolicy.can_create_vehicle(FREE_PLAN, 1)
        assert exc.value.status_code == 402
        assert "free" in exc.value.detail
        assert isinstance(exc.value, HTTPException)

    def test_driver_message_reports_the_driver_limit(self):
        # The message used to interpolate max_vehicle for the driver cap.
        with pytest.raises(PlanPolicyError) as exc:
            PlanPolicy.can_add_driver(GROWTH_PLAN, 7)
        assert "7 driver(s)" in exc.value.detail

    def test_unlimited_plan_never_blocks(self):
        PlanPolicy.can_create_vehicle(FLEET_PLAN, 10_000)
        PlanPolicy.can_add_driver(FLEET_PLAN, 10_000)

    def test_growth_boundaries(self):
        PlanPolicy.can_create_vehicle(GROWTH_PLAN, 4)   # 5th vehicle allowed
        PlanPolicy.can_add_driver(GROWTH_PLAN, 6)       # 7th driver allowed
        with pytest.raises(PlanPolicyError):
            PlanPolicy.can_create_vehicle(GROWTH_PLAN, 5)
        with pytest.raises(PlanPolicyError):
            PlanPolicy.can_add_driver(GROWTH_PLAN, 7)

    def test_status_gate_blocks_before_quota(self):
        with pytest.raises(PlanPolicyError) as exc:
            PlanPolicy.assert_can_add_vehicle(FLEET_PLAN, "canceled", 0)
        assert "canceled" in exc.value.detail

    def test_past_due_may_still_consume_quota(self):
        PlanPolicy.assert_can_add_vehicle(GROWTH_PLAN, "past_due", 0)
        PlanPolicy.assert_can_onboard_driver(GROWTH_PLAN, "past_due", 0)

    def test_property_support_is_fleet_only(self):
        PlanPolicy.assert_property_support(FLEET_PLAN)
        with pytest.raises(PlanPolicyError):
            PlanPolicy.assert_property_support(FREE_PLAN)


class TestBillingPriceMapping:
    def test_price_maps_to_plan_and_back(self, monkeypatch):
        from app.domain import billing

        monkeypatch.setattr(
            billing, "_PRICE_TO_PLAN", {"price_G": "growth", "price_F": "fleet"}
        )
        assert billing.price_to_plan("price_G") == "growth"
        assert billing.price_to_plan("price_F") == "fleet"

    def test_free_is_not_purchasable(self):
        from app.domain.billing import plan_to_price

        # free is the tier you hold by *not* subscribing, so it has no price.
        # Mapping it to one would let a tenant "check out" of a paid plan.
        assert plan_to_price("free") is None

    def test_unknown_price_returns_none(self):
        # Fail closed: an unrecognised price must never grant a tier.
        from app.domain.billing import price_to_plan

        assert price_to_plan("price_does_not_exist") is None
        assert price_to_plan("") is None
        assert price_to_plan(None) is None
