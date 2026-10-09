from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator, field_validator
from typing import Any, Dict, Literal, Optional
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
    
    
# class BookingTypesConfig(BaseModel):
#     airport: Optional[BookingTypeConfig] = Field(
#         None,
#         description="Configuration for airport transfer bookings."
#     )
#     dropoff: Optional[BookingTypeConfig] = Field(
#         None,
#         description="Configuration for point-to-point / dropoff bookings."
#     )
#     hourly: Optional[BookingTypeConfig] = Field(
#         None,
#         description="Configuration for hourly / charter bookings."
#     )

class AllowedPayment(BaseModel):
    is_allowed: Optional[bool] = Field(None, description="Decide to display a specific payment method or not")
class BookingConfig(BaseModel):
    allow_guest_bookings: Optional[bool] = Field(
        None,
        description="Allow riders to book without creating an account."
    )
    show_vehicle_images: Optional[bool] = Field(
        None,
        description="Show vehicle images in the booking flow."
    )
    allowed_payment_method: Optional[Dict[str, AllowedPayment]]
    types: Optional[Dict[str,  BookingTypeConfig]] = Field(
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


class PayRule(BaseModel):
    type: Literal["percent", "flat"]
    value: float = Field(..., ge=0, description="Percent of the fare (0-100), or flat dollars per ride.")

    @model_validator(mode="after")
    def _percent_cap(self):
        if self.type == "percent" and self.value > 100:
            raise ValueError("A percent rule cannot exceed 100")
        return self


class DriverPayConfig(BaseModel):
    """Current driver pay policy. History lives in bookings.driver_earning, not here."""
    default: PayRule
    in_house: Optional[PayRule] = Field(None, description="Overrides default for in-house drivers.")
    outsourced: Optional[PayRule] = Field(None, description="Overrides default for outsourced drivers.")


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
    driver_pay: Optional[DriverPayConfig] = Field(
        None,
        description="Driver pay policy applied to rides completed from now on. Unset = no earnings are recorded."
    )
class UpdateTenantSetting(BaseModel):
    zelle_number: Optional[str] =Field(None)
    zelle_email: Optional[EmailStr] =Field(None)
    rider_feedback_form: Optional[str] =Field(None)
    driver_feedback_form: Optional[str] =Field(None)

    
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
    stc_rate: Optional[float] = Field(None) #For airports only  [STC(Surface Transport Charge)]
    gratuity_rate: Optional[float] = Field(None) #For airports only  [Percentage]
    airport_gate_fee: Optional[float] = Field(None) #For airports only  [flat fee]
    meet_and_greet_fee: Optional[float] = Field(None) #For airports only  [flat fee]
    
    
# Keep in sync with BRAND_FONTS in maison_frontend/app/src/utils/brandFonts.ts.
BRAND_FONTS = {"DM Sans", "Work Sans", "Inter", "Manrope", "Lexend", "Geist",
               "Instrument Serif", "Playfair Display", "Fraunces", "Cormorant"}


class TenantBrandingUpdate(BaseModel):
    theme: Optional[str] = None

    # colors
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    surface_color: Optional[str] = None
    text_color: Optional[str] = None
    text_muted_color: Optional[str] = None
    button_text_color: Optional[str] = None

    # fonts: a catalog name, or "" to go back to the platform default
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    font_accent: Optional[str] = None
    # where the fonts apply: rider app only (default), + driver app, + landing page
    font_scope: Optional[Literal["rider", "rider_driver", "all"]] = None

    # assets
    favicon_url: Optional[str] = None
    logo_url: Optional[str] = None

    slug: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    enable_branding: Optional[bool] = None
    phone: Optional[str] = None
    @field_validator('font_heading', 'font_body', 'font_accent')
    @classmethod
    def validate_font(cls, value):
        if value and value not in BRAND_FONTS:
            raise ValueError(f"Unsupported font: {value}")
        return value

    @field_validator('slug', mode='before')
    def validate_slug(cls, value:str) -> any:
        if value != None:
            return value.lower().strip().replace(' ', '-').replace('_','-')
        else: return value
    class Config:
        json_schema_extra = {
            "example": {
                "theme": "dark",
                "primary_color": "#7c3aed",
                "secondary_color": "#a78bfa",
                "accent_color": "#6d28d9",
                "background_color": "#0a0a12",
                "surface_color": "#13131f",
                "text_color": "#ffffff",
                "text_muted_color": "#6b7280",
                "button_text_color": "#ffffff",
                "logo_url": "https://bls.usemaison.io/logo.png",
                "favicon_url": "https://bls.usemaison.io/favicon.ico",
                "slug": "bls",
                "email_from_name": "BLS Transportation",
                "email_from_address": "rides@bls.usemaison.io",
                "enable_branding": True,
                "phone": "+12345678"
            }
        }
class TenantPricingUpdate(BaseModel):
    base_fare: Optional[float] = None
    per_mile_rate: Optional[float] = None
    per_minute_rate: Optional[float] = None
    per_hour_rate: Optional[float] = None
    cancellation_fee: Optional[float] = None
    discounts: Optional[bool] = None


class TenantBrandingResponse(TenantBrandingUpdate):
    # id: int
    tenant_id: int
    # theme: str
    # primary_color: Optional[str]
    # secondary_color: Optional[str]
    # accent_color: Optional[str]
    # favicon_url: Optional[str]
    # slug: Optional[str]
    # email_from_name: Optional[str]
    # email_from_address: Optional[str]
    # logo_url: Optional[str]
    # enable_branding: bool
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
    


class PricingScenarioRequest(BaseModel):
    """Unsaved pricing values to preview; any field left out uses the saved value."""
    base_fare: Optional[float] = Field(None, ge=0)
    per_mile_rate: Optional[float] = Field(None, ge=0)
    per_minute_rate: Optional[float] = Field(None, ge=0)
    per_hour_rate: Optional[float] = Field(None, ge=0)


class PricingScenario(BaseModel):
    service_type: str
    vehicle_category: str
    label: str
    distance_miles: Optional[float] = None
    hours: Optional[float] = None
    total: float
    deposit: float


class PricingScenarioResponse(BaseModel):
    avg_speed_mph: float
    scenarios: list[PricingScenario]
