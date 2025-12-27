from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re
# from .tenant import TenantProfile
# from .tenant_setting import Tenant

class TenantProfile(BaseModel):
    # tenant_id:str
    company_name: str
class TenantSettings(BaseModel):
    slug: Optional[str] = None
    enable_branding: Optional[bool] = None
    logo_url: Optional[str] = None
    rider_tiers_enabled: Optional[bool] = None
    per_minute_rate: Optional[float] = None
    per_mile_rate: Optional[float] = None
    per_hour_rate: Optional[float] = None
    cancellation_fee: Optional[float] = None
class TenantSlugResponse(BaseModel):
    settings: TenantSettings 
    profile: TenantProfile

class TenantSetupResponse(BaseModel):
    settings: TenantSettings 
    profile: TenantProfile
    