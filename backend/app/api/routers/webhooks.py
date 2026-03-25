"""
Stripe webhook HTTP routes.

There are two endpoints on purpose — they use different Stripe webhook signing secrets:

- POST /api/v1/webhooks/
  Main Stripe account webhook (WEBHOOK_SECRET). Tenant subscription billing, checkout
  sessions for plans, etc. Configure this URL in the Stripe Dashboard under your
  platform account's Webhooks.

- POST /api/v1/webhooks/tenant/connect
  Stripe Connect webhook (CONNECT_WEBHOOK_SECRET). Events are scoped to Connect accounts
  (event includes `account`). Used for Express account lifecycle, saving stripe_account_id
  after onboarding, and Connect-side payments. Configure as a separate Connect webhook
  endpoint in Stripe (Connect settings / webhook for connected accounts).
"""
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, FastAPI, Response, UploadFile,status, Request
from fastapi.params import Depends
from app.schemas.general import StandardResponse as resp
from app.utils.logging import logger
from typing import Optional
from app.models import vehicle_category_rate
from ..services.stripe_services.webhooks import WebhookServices, get_ebhook_services

router = APIRouter(
    prefix = "/api/v1/webhooks",
    tags = ["Webhooks"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Stripe platform webhook",
    description=(
        "Receives events signed with **WEBHOOK_SECRET**: subscription checkout, subscription updates, "
        "`invoice.paid`, etc. Configure in Stripe Dashboard → Developers → Webhooks (platform account)."
    ),
    response_description="Handler status payload.",
)
async def stripe_platform_webhook(
    request: Request, stripe_service: WebhookServices = Depends(get_ebhook_services)
):
    """
    Main platform webhook: subscription checkout, subscription updates, invoice events.
    Verified with WEBHOOK_SECRET. Not used for Connect account onboarding (use /tenant/connect).
    """
    webhooks = await stripe_service.webhook(request)
    return webhooks


@router.post(
    "/tenant/connect",
    status_code=201,
    summary="Stripe Connect webhook",
    description=(
        "Receives events signed with **CONNECT_WEBHOOK_SECRET**; includes **`account`** (connected acct id). "
        "Used for `account.updated`, `payment_intent.succeeded`, etc. Configure under Connect webhook settings."
    ),
    response_description="Handler status / success payload.",
)
async def tenant_connect_webhook(
    request: Request,
    webhook_service: WebhookServices = Depends(get_ebhook_services),
):
    """
    Connect-only webhook receiver. Stripe sends events related to connected accounts here
    (e.g. account.updated, payment_intent.succeeded on the connected account).
    Verified with CONNECT_WEBHOOK_SECRET — do not use the same secret as POST /webhooks/.
    """

    webhook = await webhook_service.tenant_connect_webhooks(request=request)
    return webhook


