from fastapi import APIRouter, Request, status, Path
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import general, subscription
from .dependencies import is_tenants
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
    response_model=general.StandardResponse[subscription.CheckoutSessionResponse],
    summary="Upgrade or change subscription",
    description="Stripe portal / upgrade flow for existing tenant subscription. Requires **tenant** JWT.",
    response_description="Checkout or portal payload.",
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


@router.post(
    "/webhooks",
    status_code=status.HTTP_201_CREATED,
    summary="[Legacy] Stripe subscription webhook",
    description=(
        "Alternate entrypoint for subscription webhooks via **`StripeService.webhook`**. "
        "Prefer **`POST /api/v1/webhooks/`** for platform events; keep secrets aligned."
    ),
    response_description="Webhook handler result.",
)
async def subscription_stripe_webhooks(
    request: Request,
    stripe_service: StripeService = Depends(get_unauthorized_subscription_service),
):
    webhooks = await stripe_service.webhook(request)
    return webhooks
