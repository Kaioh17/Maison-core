"""Server-side mapping between Stripe price ids and Maison plan tiers.

The plan a tenant receives must be derived from the price they actually paid
for, never from a client-supplied field. `product_type` arrives in the request
body, so trusting it lets a tenant check out the growth price while asking for
fleet quotas.
"""
from typing import Optional

from app.config import Settings
from app.domain.plans import PlanName

_settings = Settings()

# Built once at import. Values come from the same Stripe price ids the frontend
# holds in VITE_STRIPE_PRICE_* (maison_frontend/app/src/config.ts).
# `free` has no Stripe price and is deliberately absent: it is the tier a tenant
# holds by *not* having a subscription, so it is never checked out. The retired
# `starter` price is likewise unmapped, which makes price_to_plan fail closed on
# any stale checkout link still pointing at it.
_PLAN_TO_PRICE = {
    PlanName.GROWTH.value: _settings.stripe_price_growth,
    PlanName.FLEET.value: _settings.stripe_price_fleet,
}

_PRICE_TO_PLAN = {
    price: plan for plan, price in _PLAN_TO_PRICE.items() if price
}


def price_to_plan(price_id: str) -> Optional[str]:
    """Resolve a Stripe price id to a plan name, or None if unrecognised."""
    if not price_id:
        return None
    return _PRICE_TO_PLAN.get(str(price_id).strip())


def plan_to_price(plan_name: str) -> Optional[str]:
    """Resolve a plan name to its configured Stripe price id."""
    if not plan_name:
        return None
    return _PLAN_TO_PRICE.get(str(plan_name).strip().lower())
