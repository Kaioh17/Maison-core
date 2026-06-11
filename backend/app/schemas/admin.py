from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate
from .tenant import TenantProfile, TenantStats
from .driver import DriverResponse
from .user import UserResponse
from .tenant_setting import (
    TenantBrandingResponse,
    TenantPricingResponse,
    TenantBookingPublic,
)

import re

class AdminBase(BaseModel):
    email: EmailStr = Field()
    # phone_no: str = Field(..., pattern = r'^\+?[\d\s\-\(\)]+$')
    first_name: str = Field(..., min_length=1, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)


    @field_validator('email')
    def validate_email(cls, v):
        return v.lower()
class CreateAdmin(AdminBase):
    password: str = Field(...)
class AdminResponse(AdminBase):
    pass


class AdminComposeEmail(BaseModel):
    """Payload for `POST /api/v1/admin/email/compose`."""
    to_tenant_id: int = Field(..., ge=1, description="Tenant to send to.")
    from_alias: str = Field(
        ...,
        description="Mailbox local part (e.g. 'noreply', 'support', 'billing', 'hello').",
        pattern=r'^[a-z0-9._+-]+$',
    )
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, description="Plain-text message body.")


"""Admin tenant-detail schemas.

These power `GET /api/v1/admin/tenants/{tenant_id}` — a single, fully
expanded view of one tenant aggregated across every model that belongs to
it. Sub-views are intentionally read-only/non-raising so legacy rows never
break the aggregate response; they reuse the existing per-role response
schemas where those are already safe to build from ORM objects.
"""


class AdminTenantAccount(BaseModel):
    """The tenant's own login/account record (`tenants` table)."""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    full_name: Optional[str] = None  # computed property
    phone_no: str
    role: str
    is_verified: bool
    is_active: bool
    created_on: datetime
    updated_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminTenantSettingsView(BaseModel):
    """`tenants_settings` row; `config` left as raw JSONB to stay lenient."""
    tenant_id: int
    rider_tiers_enabled: Optional[bool] = None
    zelle_number: Optional[str] = None
    zelle_email: Optional[str] = None
    rider_feedback_form: Optional[str] = None
    driver_feedback_form: Optional[str] = None
    config: Optional[dict] = None
    created_on: datetime
    updated_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminBookingView(BaseModel):
    """Flat, non-raising view of a `bookings` row for the admin console."""
    id: int
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    rider_id: Optional[int] = None
    service_type: Optional[str] = None
    airport_service: Optional[str] = None
    booking_status: Optional[str] = None
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    pickup_location: Optional[str] = None
    pickup_time: Optional[datetime] = None
    dropoff_location: Optional[str] = None
    dropoff_time: Optional[datetime] = None
    country: Optional[str] = None
    hours: Optional[float] = None
    estimated_price: Optional[float] = None
    notes: Optional[str] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminPayoutView(BaseModel):
    """`payouts` row — driver payout via Stripe Connect."""
    id: int
    driving_id: Optional[int] = None
    booking_id: Optional[int] = None
    stripe_transfer_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    created_on: datetime
    updated_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminTransactionView(BaseModel):
    """`transactions` row — rider charge / platform fee."""
    id: int
    booking_id: Optional[int] = None
    stripe_payment_intent_id: Optional[str] = None
    amount: float
    platform_fee_amount: Optional[float] = None
    currency: str
    status: str
    created_on: datetime
    updated_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminTenantCounts(BaseModel):
    """Aggregate counts of the tenant's related records."""
    drivers: int = 0
    riders: int = 0
    vehicles: int = 0
    bookings: int = 0
    booking_pricing: int = 0
    payouts: int = 0
    transactions: int = 0


class LogsResponse(BaseModel):
    log_file: str
    lines: list[str]
    total_lines: int
    environment: str


class AdminTenantDetail(BaseModel):
    """Everything known about a single tenant, grouped by model/domain."""
    account: AdminTenantAccount
    profile: Optional[TenantProfile] = None
    stats: Optional[TenantStats] = None
    settings: Optional[AdminTenantSettingsView] = None
    branding: Optional[TenantBrandingResponse] = None
    pricing: Optional[TenantPricingResponse] = None
    booking_pricing: list[TenantBookingPublic] = Field(default_factory=list)
    drivers: list[DriverResponse] = Field(default_factory=list)
    riders: list[UserResponse] = Field(default_factory=list)
    vehicles: list[VehicleResponse] = Field(default_factory=list)
    bookings: list[AdminBookingView] = Field(default_factory=list)
    payouts: list[AdminPayoutView] = Field(default_factory=list)
    transactions: list[AdminTransactionView] = Field(default_factory=list)
    counts: AdminTenantCounts = Field(default_factory=AdminTenantCounts)

    model_config = {"from_attributes": True}
