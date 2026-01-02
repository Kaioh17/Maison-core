from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re
from enum import Enum
from fastapi import UploadFile, Form

class DriverType(str, Enum):
    OUTSOURCED = "outsourced"
    IN_HOUSE = "in_house"
"""Tenants Schemas"""
class TenantCreate(BaseModel):
    email: EmailStr = Form(...)
    first_name: str = Form(..., min_length=1, max_length=200)
    last_name: str = Form(..., min_length=1, max_length=200)
    password: str = Form(min_length=8)
    phone_no: str = Form(..., pattern = r'^\+?[\d\s\-\(\)]+$')
    company_name: str = Form(..., min_length=1, max_length=200)
    # logo_url: Optional[UploadFile] = None
    slug: str = Form(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    address: Optional[str] = Form(None)
    city: str = Form(..., min_length=1, max_length=100)
    drivers_count: int = Form(default=0, ge=0)

    @field_validator('email')
    def validate_email(cls, v):
        return v.lower()
    @field_validator('slug', mode='before')
    def validate_slug(cls, value:str) -> any:
        if value != None:
            return value.lower().strip().replace(' ', '-').replace('_','-')
    # @field_validator('slug')
    # def validate_slug(cls, v):
    #     if not re.match(r'^[a-z0-9-]+$', v):
    #         raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
    #     return v.lower()
    
    @field_validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
class TenantUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=200)
    last_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone_no: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    logo_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    drivers: Optional[int] = Field(None, ge=0)
    plan: Optional[str] = Field(None, pattern=r'^(free|basic|premium|enterprise)$')
    is_active: Optional[bool] = None
    
    
class TenantProfile(BaseModel):
    tenant_id: int = Field(exclude=True)
    company_name: str = Field(..., max_length=200)
    logo_url: Optional[str] = Field(None)
    slug: str = Field()
    address: Optional[str] = Field(None)
    city: str = Field()
    role: str = Field(default="tenant")
    stripe_customer_id: Optional[str] = Field(None)
    stripe_account_id: Optional[str] = Field(None)

    subscription_status: Optional[str] = Field(default="free")
    subscription_plan: Optional[str] = Field(default="free")
    created_on: datetime = Field()
    updated_on: Optional[datetime] = Field(None)
    company: Optional[str] = Field(None)  # Computed property

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "tenant_id": 1,
                "company_name": "Acme Corp",
                "logo_url": "https://example.com/logo.png",
                "slug": "acme-corp",
                "address": "123 Main St",
                "city": "New York",
                "role": "tenant",
                "stripe_customer_id": "cus_123456",
                "stripe_account_id": "acct_123456",
                "subscription_status": "active",
                "subscription_plan": "premium",
                "created_on": "2024-01-01T00:00:00Z",
                "updated_on": None,
                "company": "Acme Corp"
            }
        }
class TenantInfo(BaseModel):
    id: int = Field()
    email: EmailStr = Field()
    first_name: str = Field(..., max_length=200)
    last_name: str = Field(..., max_length=200)
    phone_no: str = Field(..., max_length=200)
    created_on: datetime = Field()
    updated_on: Optional[datetime] = Field(None)
    full_name: Optional[str] = Field(None)  # Computed property
    is_verified: bool = Field(...)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "tenant@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_no": "+1234567890",
                "created_on": "2024-01-01T00:00:00Z",
                "updated_on": None,
                "full_name": "John Doe"
            }
        }

class TenantStats(BaseModel):
    tenant_id: int = Field(exclude=True)
    drivers_count: int = Field()
    daily_ride_count: int = Field(default=0)
    last_ride_count_reset: Optional[datetime] = Field(None)
    total_ride_count: int = Field(default=0)
    created_on: datetime = Field()
    updated_on: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "tenant_id": 1,
                "drivers_count": 10,
                "daily_ride_count": 25,
                "last_ride_count_reset": "2024-01-01T00:00:00Z",
                "total_ride_count": 1000,
                "created_on": "2024-01-01T00:00:00Z",
                "updated_on": None
            }
        }
    
class TenantRsponse(BaseModel):
    tenants: TenantInfo = Field()
    profile: TenantProfile = Field()
    stats: TenantStats = Field()
class TenantResponse(TenantInfo):
    profile: TenantProfile = Field()
    stats: TenantStats = Field()

   
"""schema to onboard driver """
class OnboardDriverBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    driver_type: DriverType

class OnboardDriver(OnboardDriverBase):
    pass
class OnboardDriverResponse(OnboardDriverBase):
    id: int
    driver_token: str
    created_on: datetime
    
class AssignDriver(BaseModel):
    """
    AssignDriver schema for assigning a driver to a booking
    """
    driver_id: int = Field(default=None)
    override: bool = Field(default=False, description="Flag that allows changing from one driver id to another")

class TenantLogin(BaseModel):
    email: EmailStr
    password: str


