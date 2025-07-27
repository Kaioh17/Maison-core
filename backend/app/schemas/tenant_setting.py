from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class UpdateTenantSetting(BaseModel):
    theme: str
    logo_url: str 
    slug: str
    enable_branding: bool
    #Fare 
    base_fare: float
    per_minute_rate: float
    per_mile_rate: float
    per_hour_rate: float
    #rider setings 
    rider_tiers_enabled: bool
    cancellation_fee: float 

    discounts: bool

class TenantResponse(UpdateTenantSetting):
    id: int 
    updated_on: Optional[datetime]