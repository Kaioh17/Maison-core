"""Canonical subscription plan definitions.

Single source of truth for what each tier allows. The frontend currently
duplicates these numbers as marketing copy; `GET /api/v1/subscription/limits`
exists so it can stop doing that.
"""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class PlanName(str, Enum):
    FREE = "free"
    GROWTH = "growth"
    FLEET = "fleet"


class SubStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INACTIVE = "inactive"  # legacy default already present in the DB


# Statuses allowed to consume quota. past_due is deliberately included: a failed
# card should not instantly break a tenant's operations, so it gets a grace period.
ENTITLED_STATUSES = frozenset({
    SubStatus.ACTIVE.value,
    SubStatus.TRIALING.value,
    SubStatus.PAST_DUE.value,
})


@dataclass(frozen=True)
class Plan:
    name: str
    max_vehicle: Optional[int]        # None == unlimited
    max_driver_count: Optional[int]   # None == unlimited
    maison_fee: float
    allow_property_support: bool
    allow_analytics: bool
    # List price in cents, mirrored from the Stripe Price object this tier maps
    # to in `domain/billing.py`. Stripe remains the system of record for what is
    # actually charged -- this exists only so the public pricing pages can render
    # one number that the app agrees with. **If you change a price in Stripe, you
    # must change it here too**; nothing enforces the link.
    monthly_price_cents: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# Unlimited is None rather than math.inf: these values are serialized by the
# limits endpoint, and json.dumps(math.inf) emits the bare token `Infinity`,
# which is invalid JSON and throws in the browser's JSON.parse. None -> null.
#
# The take rate declines as the subscription price rises: the higher tier is
# partly buying a lower cut of their own revenue, which is what makes upgrading
# rational for an operator with volume. See maison_frontend/PRICING_RATIONALE.md.
FREE_PLAN = Plan("free", 1, 1, 0.03, False, False, monthly_price_cents=0)
GROWTH_PLAN = Plan("growth", 5, 7, 0.02, False, True, monthly_price_cents=29999)
FLEET_PLAN = Plan("fleet", None, None, 0.01, True, True, monthly_price_cents=39999)

# Ordered cheapest -> most expensive. This is the upgrade ladder, and the order
# the pricing pages render in; keep it explicit rather than relying on dict
# insertion order so a reordered literal can't silently reshuffle the UI.
PLAN_LADDER = (FREE_PLAN, GROWTH_PLAN, FLEET_PLAN)

PLAN_REGISTRY = {p.name: p for p in PLAN_LADDER}

# The 100%-off founding-operator coupon (see stripe_tier_service.py) is only
# emailed to the first this-many tenants. Frontend shows the countdown as
# marketing copy; the coupon code itself is never sent to the client.
FOUNDING_OPERATOR_SLOTS = 10


def resolve_plan(subscription_plan) -> Plan:
    """Map a stored subscription_plan value onto a Plan. Never raises.

    None, "", "free" and any unrecognised value all fall back to FREE_PLAN.
    The column defaults to "free", so a lookup that raises would 500 every
    tenant who has never subscribed.
    """
    if not subscription_plan:
        return FREE_PLAN
    return PLAN_REGISTRY.get(str(subscription_plan).strip().lower(), FREE_PLAN)


def resolve_status(subscription_status) -> str:
    """Normalise a stored or Stripe-supplied status. Never raises."""
    if not subscription_status:
        return SubStatus.INACTIVE.value
    candidate = str(subscription_status).strip().lower()
    if candidate in {s.value for s in SubStatus}:
        return candidate
    return SubStatus.INACTIVE.value


def is_entitled(subscription_status) -> bool:
    """True when the subscription state permits consuming quota."""
    return resolve_status(subscription_status) in ENTITLED_STATUSES
