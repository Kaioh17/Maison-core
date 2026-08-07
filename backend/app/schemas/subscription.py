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
    plan: str
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