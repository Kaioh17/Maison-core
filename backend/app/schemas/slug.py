from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal, Union
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


class StorefrontAction(BaseModel):
    label: str
    route: str


class StorefrontLink(BaseModel):
    label: str
    value: str
    href: str


class StorefrontFooter(BaseModel):
    copyright: str
    links: list[StorefrontLink] = Field(default_factory=list)


class DefaultStorefrontCard(BaseModel):
    title: str
    description: str
    primary_cta: StorefrontAction
    secondary_cta: Optional[StorefrontAction] = None


class DefaultStorefrontSchema(BaseModel):
    template: Literal["default"]
    tenant_name: str
    wordmark: str
    welcome_label: str
    hero_title: str
    hero_description: str
    rider_card: DefaultStorefrontCard
    driver_card: DefaultStorefrontCard
    footer: StorefrontFooter

    @validator("template", pre=True)
    def normalize_default_template(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class PremiumStorefrontHero(BaseModel):
    title: str
    supporting: str


class PremiumStorefrontCtas(BaseModel):
    primary: StorefrontAction
    secondary: StorefrontAction


class PremiumStorefrontValueProp(BaseModel):
    title: str
    description: str


class PremiumStorefrontPalette(BaseModel):
    background: str
    text: str
    accent: str
    muted: str
    button_text: str


class PremiumStorefrontSchema(BaseModel):
    template: Literal["premium"]
    tenant_name: str
    wordmark: str
    caption: str
    hero: PremiumStorefrontHero
    ctas: PremiumStorefrontCtas
    value_props: list[PremiumStorefrontValueProp]
    trust_line: str
    palette: PremiumStorefrontPalette
    footer: StorefrontFooter

    @validator("template", pre=True)
    def normalize_premium_template(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


StorefrontSchema = Union[DefaultStorefrontSchema, PremiumStorefrontSchema]