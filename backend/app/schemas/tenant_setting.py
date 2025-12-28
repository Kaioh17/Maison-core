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
    ALL = "all"
class UpdateTenantSetting(BaseModel):
    rider_tiers_enabled: Optional[bool] = None
    updated_on: Optional[datetime] = None
    config:Optional[dict]=None


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
    id: int
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

class TenantPricingResponse(BaseModel):
    id: int
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
class TenantResponse(UpdateTenantSetting):
    id: int 
    tenant_id: int
    created_on: datetime
    updated_on: Optional[datetime] = None
class TenantConfigResponse(BaseModel):
    # config_dict = {"settings":settings.__dict__, "pricing":pricing.__dict__, "branding":branding.__dict__}
    settings: Optional[TenantResponse] = None
    pricing: Optional[TenantPricingResponse] = None
    branding: Optional[TenantBrandingUpdate] = None
    


class updated_visuals(BaseModel):
    logo_url: Optional[str] = None
