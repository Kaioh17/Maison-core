from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re
# from .tenant import TenantProfile
from .tenant_setting import *

class TenantProfile(BaseModel):
    # tenant_id:str
    company_name: str
class TenantSettings(BaseModel):
   
    rider_tiers_enabled: Optional[bool] = None
    config: Optional[dict] = None
    
class TenantSlugResponse(BaseModel):
    settings: TenantSettings 
    profile: TenantProfile
    branding: TenantBrandingPublic
    

class TenantSetupResponse(BaseModel):
    settings: TenantSettings 
    profile: TenantProfile
    branding: TenantBrandingPublic
    pricing: Optional[TenantPricingPublic] =None