from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator, field_validator
from typing import Optional
import re
class ConfigTypes(str, Enum):
    BRANDING = "branding"
    PRICING =  "pricing"
    SETTING = "setting"
    BOOKING = "booking"
    ALL = "all"
class DepositType(str, Enum):
    PERCENTAGE = "percentage"
    FLAT =  "flat"
from typing import Optional
from pydantic import BaseModel, Field


class BookingTypeConfig(BaseModel):
    is_deposit_required: Optional[bool] = Field(None,description="Whether this booking type requires a deposit to confirm.")
class BookingTypesConfig(BaseModel):
    airport: Optional[BookingTypeConfig] = Field(
        None,
        description="Configuration for airport transfer bookings."
    )
    dropoff: Optional[BookingTypeConfig] = Field(
        None,
        description="Configuration for point-to-point / dropoff bookings."
    )
    hourly: Optional[BookingTypeConfig] = Field(
        None,
        description="Configuration for hourly / charter bookings."
    )


class BookingConfig(BaseModel):
    allow_guest_bookings: Optional[bool] = Field(
        None,
        description="Allow riders to book without creating an account."
    )
    show_vehicle_images: Optional[bool] = Field(
        None,
        description="Show vehicle images in the booking flow."
    )
    types: Optional[BookingTypesConfig] = Field(
        None,
        description="Per-service-type booking behavior configuration."
    )


class BrandingConfig(BaseModel):
    button_radius: Optional[int] = Field(
        None,
        description="Border radius (in pixels) for primary buttons in the UI."
    )
    font_family: Optional[str] = Field(
        None,
        description="Primary font family used across the tenant’s interface."
    )


class FeaturesConfig(BaseModel):
    vip_profiles: Optional[bool] = Field(
        None,
        description="Enable VIP rider profiles with saved preferences."
    )
    show_loyalty_banner: Optional[bool] = Field(
        None,
        description="Display a loyalty/status banner in the rider experience."
    )


class TenantConfig(BaseModel):
    booking: Optional[BookingConfig] = Field(
        None,
        description="Configuration related to booking behavior and flows."
    )
    branding: Optional[BrandingConfig] = Field(
        None,
        description="UI branding options for this tenant."
    )
    features: Optional[FeaturesConfig] = Field(
        None,
        description="Feature toggles controlling optional product capabilities."
    )
class UpdateTenantSetting(BaseModel):
    rider_tiers_enabled: Optional[bool] = None
    config:Optional[TenantConfig]=None
    
class TenantBookingPublic(BaseModel):
    deposit_fee: Optional[float] = Field(None)
    deposit_type: Optional[DepositType] = Field(None)
    service_type: str = Field(...)
    updated_on: Optional[datetime] = Field(None)
class TenantBookingUpdate(BaseModel):
    # service_type: str=Field(exclude=True)  
    # updated_on: datetime = Field(exclude=True)
    deposit_fee: Optional[float] = Field(None)
    deposit_type: Optional[DepositType] = Field(None)
class TenantBrandingUpdate(BaseModel):
    theme: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    favicon_url: Optional[str] = None
    slug: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    logo_url: Optional[str] = None
    enable_branding: Optional[bool] = None

    @field_validator('slug', mode='before')
    def validate_slug(cls, value:str) -> any:
        if value != None:
            return value.lower().strip().replace(' ', '-').replace('_','-')
        else: return value
        
class TenantPricingUpdate(BaseModel):
    base_fare: Optional[float] = None
    per_mile_rate: Optional[float] = None
    per_minute_rate: Optional[float] = None
    per_hour_rate: Optional[float] = None
    cancellation_fee: Optional[float] = None
    discounts: Optional[bool] = None


class TenantBrandingResponse(BaseModel):
    # id: int
    tenant_id: int
    theme: str
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    favicon_url: Optional[str]
    slug: Optional[str]
    email_from_name: Optional[str]
    email_from_address: Optional[str]
    logo_url: Optional[str]
    enable_branding: bool
    created_on: datetime
    updated_on: Optional[datetime]

    class Config:
        from_attributes = True

class TenantBrandingPublic(TenantBrandingResponse):
    # id: int = Field(exclude=True)
    tenant_id: int = Field(exclude=True)
    created_on: datetime = Field(exclude=True)
    updated_on: Optional[datetime] = Field(exclude=True)
class TenantPricingResponse(BaseModel):
    # id: int
    tenant_id: int
    base_fare: float
    per_mile_rate: float
    per_minute_rate: Optional[float]
    per_hour_rate: float
    cancellation_fee: float
    discounts: bool
    created_on: datetime
    updated_on: Optional[datetime]

    class Config:
        from_attributes = True
class TenantPricingPublic(TenantPricingResponse):
    # id: int = Field(exclude=True)
    tenant_id: int = Field(exclude=True)
    created_on: datetime = Field(exclude=True)
    updated_on: Optional[datetime] = Field(exclude=True)
class TenantResponse(UpdateTenantSetting):
    pass
    # id: int 
    # tenant_id: in
    # created_on: datetime
    # updated_on: Optional[datetime] = None
class TenantConfigResponse(BaseModel):
    # config_dict = {"settings":settings.__dict__, "pricing":pricing.__dict__, "branding":branding.__dict__}
    settings: Optional[TenantResponse] = None
    pricing: Optional[TenantPricingPublic] = None
    branding: Optional[TenantBrandingPublic] = None
    booking: Optional[list[TenantBookingPublic]] = None


class updated_visuals(BaseModel):
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    
