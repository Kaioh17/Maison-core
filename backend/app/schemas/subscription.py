from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate

class SubscriptionCreate(BaseModel):
    price_id: str
    product_type: str
    
class CheckoutSessionResponse(BaseModel):
    # 'Checkout_session_url':checkout_session.url,
    #                                     'tenant_id': self.current_user.id,
    #                                     'customer_id': checkout_session.customer,
    #                                     'product_type': product_type,
    #                                     'sub_total': checkout_session.amount_subtotal}
    
    Checkout_session_url: str
    # tenant_id: int
    customer_id: str
    product_type: str
    sub_total: int
    
class QuotaUsage(BaseModel):
    used: int
    allowed: Optional[int] = None      # null == unlimited
    remaining: Optional[int] = None    # null == unlimited
    over_limit: bool = False


class PlanCatalogEntry(BaseModel):
    """One tier as the pricing UI needs to render it. `null` == unlimited.

    Carries the list price so that the public marketing page and the in-app
    pricing table render from the same payload and cannot disagree. Stripe stays
    the system of record for what is actually charged; this is the display copy.
    """
    name: str
    max_vehicle: Optional[int] = None
    max_driver_count: Optional[int] = None
    maison_fee: float
    allow_property_support: bool
    allow_analytics: bool
    # Cents, to avoid float money. 0 == free, which is not purchasable.
    monthly_price_cents: int = 0


class PlanLimitsResponse(BaseModel):
    """Authoritative plan limits + live usage, so clients stop hardcoding them."""
    plan: Optional[str] = None  # null == unsubscribed (no plan at all)
    status: str
    is_entitled: bool
    maison_fee: float
    allow_property_support: bool
    vehicles: QuotaUsage
    drivers: QuotaUsage
    # Every tier, cheapest first -- lets the pricing pages render the full
    # comparison table from this one call instead of duplicating the ladder.
    catalog: list[PlanCatalogEntry] = []


class PortalSessionResponse(BaseModel):
    """A tier change is confirmed in Stripe's Billing Portal, not billed
    server-side -- this URL shows the card on file and the prorated amount
    before anything charges. See directives.md billing-confirm-2026-08."""
    portal_url: str
    tenant_id: int
    customer_id: str
    product_type: str

class BillingDiscount(BaseModel):
    name: Optional[str] = None
    percent_off: Optional[float] = None
    amount_off: Optional[int] = None          # cents
    duration: Optional[str] = None            # once | repeating | forever
    duration_in_months: Optional[int] = None


class BillingPaymentMethod(BaseModel):
    brand: Optional[str] = None
    last4: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None


class BillingInvoice(BaseModel):
    id: str
    number: Optional[str] = None
    created: int                              # unix seconds
    status: Optional[str] = None              # paid | open | void | uncollectible
    amount_due: int = 0                       # cents
    amount_paid: int = 0                      # cents
    currency: str = "usd"
    hosted_invoice_url: Optional[str] = None
    invoice_pdf: Optional[str] = None


class BillingStripe(BaseModel):
    """What Stripe is actually charging. Stripe is the system of record for
    money; nothing here is derived from the plan catalogue."""
    status: str
    currency: str = "usd"
    interval: Optional[str] = None            # month | year | ...
    interval_count: int = 1
    recurring_amount: int = 0                 # cents per interval at list price
    next_invoice_amount: Optional[int] = None  # cents after discounts; None when nothing is coming
    current_period_start: Optional[int] = None  # unix seconds
    current_period_end: Optional[int] = None    # next renewal, or end date if cancelling
    cancel_at_period_end: bool = False
    started_on: Optional[int] = None
    discount: Optional[BillingDiscount] = None
    payment_method: Optional[BillingPaymentMethod] = None
    invoices: list[BillingInvoice] = []


class BillingOverviewResponse(BaseModel):
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    stripe: Optional[BillingStripe] = None    # null: no subscription, or Stripe unreachable
    stripe_error: Optional[str] = None
