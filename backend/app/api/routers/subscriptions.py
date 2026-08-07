from typing import Union
from fastapi import APIRouter, Request, status, Path
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import general, subscription
from app.domain import plans
from ..services.helper_service import success_resp
from .dependencies import is_tenants
from ..services.tenants_service import TenantService, get_tenant_service, founding_operator_slots_remaining
from ..services.stripe_services import stripe_tier_service
from ..services.stripe_services.stripe_tier_service import (
    StripeService,
    get_stripe_subscription_service,
    get_unauthorized_subscription_service,
)

router = APIRouter(
    prefix="/api/v1/subscription",
    tags=["Subscription"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=general.StandardResponse[subscription.CheckoutSessionResponse],
    summary="Start subscription checkout (Stripe)",
    description=(
        "Creates a Stripe Checkout session for Maison **SaaS** plans (`price_id`, `product_type`). "
        "Requires **tenant** JWT (company billing)."
    ),
    response_description="Checkout session id / redirect URL.",
)
async def create_checkout_session(
    payload: subscription.SubscriptionCreate,
    stripe_service: StripeService = Depends(get_stripe_subscription_service),
    is_tenant=Depends(is_tenants),
):
    create_subscription = await stripe_service.create_checkout_session(
        price_id=payload.price_id, product_type=payload.product_type
    )
    return create_subscription


@router.patch(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=general.StandardResponse[
        Union[subscription.PortalSessionResponse, subscription.CheckoutSessionResponse]
    ],
    summary="Upgrade or change subscription",
    description=(
        "Returns a Stripe-hosted URL to redirect the tenant to -- never bills directly. "
        "An existing subscription gets a **Billing Portal** URL scoped to confirming this one "
        "price change (card on file + prorated amount, see `PortalSessionResponse`); a tenant "
        "with no subscription yet (free tier) gets a **Checkout session** URL instead, since "
        "there is nothing to update -- see `CheckoutSessionResponse`. Requires **tenant** JWT."
    ),
    response_description="Checkout or billing-portal redirect payload.",
)
async def upgrade_subscription(
    payload: subscription.SubscriptionCreate,
    stripe_service: StripeService = Depends(get_stripe_subscription_service),
    is_tenant=Depends(is_tenants),
):
    upgrade_sub = await stripe_service.upgrade_subscription(
        price_id=payload.price_id, product_type=payload.product_type
    )
    return upgrade_sub


@router.get(
    "/limits",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[subscription.PlanLimitsResponse],
    summary="Current plan limits and usage",
    description=(
        "Authoritative per-tier limits plus live usage counts for the calling tenant. "
        "`allowed: null` means unlimited. Requires **tenant** JWT -- deliberately not "
        "subscription-gated, since an inactive tenant must be able to read their own "
        "state to see the upgrade prompt."
    ),
    response_description="Plan, subscription status, and vehicle/driver usage.",
)
async def get_plan_limits(
    is_tenant=Depends(is_tenants),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    return await tenant_service.get_plan_limits()


# NB: must stay declared ABOVE `GET /{customer_id}`. FastAPI matches routes in
# declaration order, and that catch-all would otherwise swallow "/plans" and try
# to read it as a Stripe customer id.
@router.get(
    "/plans",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[subscription.PlanCatalogEntry]],
    summary="Public plan catalogue",
    description=(
        "Every tier with its limits, take rate, and list price, cheapest first. "
        "**Unauthenticated on purpose** -- the public marketing page renders from "
        "this, which is what stops it from disagreeing with the in-app pricing "
        "table. Contains no tenant data. Authenticated callers who also need "
        "their own usage and current plan should use `GET /subscription/limits`, "
        "which returns the same catalogue plus that state."
    ),
    response_description="The plan ladder, cheapest first.",
)
async def get_public_plans(db: Session = Depends(get_db)):
    return success_resp(
        msg="Retrieved plans",
        data=[p.to_dict() for p in plans.PLAN_LADDER],
        meta={"founding_operator_slots_remaining": founding_operator_slots_remaining(db)},
    )


@router.get(
    "/{customer_id}",
    summary="Get subscription status (placeholder)",
    description=(
        "Path includes **`customer_id`** for future use; current implementation delegates to service singleton. "
        "Requires DB session."
    ),
    response_description="Subscription status JSON.",
)
async def get_subscription(
    customer_id: str = Path(..., description="Stripe customer id (reserved for future filtering)."),
    db: Session = Depends(get_db),
):
    get_subscription_status = await stripe_tier_service.StripeService.get_customer_subscription_status()
    return {"status": get_subscription_status}

"""Deprecated endpoint"""
@router.post(
    "/webhooks",
    status_code=status.HTTP_201_CREATED,
    summary="[Legacy] Stripe subscription webhook",
    description=(
        "Alternate entrypoint for subscription webhooks via **`StripeService.webhook`**. "
        "Prefer **`POST /api/v1/webhooks/`** for platform events; keep secrets aligned."
    ),
    response_description="Webhook handler result.",
    deprecated=True
)
async def subscription_stripe_webhooks(
    request: Request,
    stripe_service: StripeService = Depends(get_unauthorized_subscription_service),
):
    # webhooks = await stripe_service.webhook(request)
    # return webhooks
    ...