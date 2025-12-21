from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator, field_validator
from typing import Optional
import re

class UpdateTenantSetting(BaseModel):
    theme: Optional[str] = None
    slug: Optional[str] = None
    enable_branding: Optional[bool] = None
    base_fare: Optional[float] = None
    per_minute_rate: Optional[float] = None
    per_mile_rate: Optional[float] = None
    per_hour_rate: Optional[float] = None
    rider_tiers_enabled: Optional[bool] = None
    cancellation_fee: Optional[float] = None
    discounts: Optional[bool] = None
    updated_on: Optional[datetime] = None

    @field_validator('slug', mode='before')
    def validate_slug(cls, value:str) -> any:
        if value != None:
            return value.lower().strip().replace(' ', '-').replace('_','-')
        
class TenantResponse(UpdateTenantSetting):
    id: int 
    tenant_id: int
    created_on: datetime
    logo_url: Optional[str] = None
    updated_on: Optional[datetime] = None

class updated_vicuals(BaseModel):
    logo_url: Optional[str] = None
