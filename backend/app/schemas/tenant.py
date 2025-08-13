from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re
from enum import Enum

class DriverType(str, Enum):
    OUTSOURCED = "outsourced"
    IN_HOUSE = "in_house"
"""Tenants Schemas"""
class TenantCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(min_length=8)
    phone_no: str = Field(..., pattern = r'^\+?[\d\s\-\(\)]+$')
    company_name: str = Field(..., min_length=1, max_length=200)
    logo_url: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    address: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    drivers_count: int = Field(default=0, ge=0)

    @field_validator('email')
    def validate_email(cls, v):
        return v.lower()
    
    @field_validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()
    
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


class TenantResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone_no: str
    company_name: str
    logo_url: Optional[str]
    slug: str
    address: Optional[str]
    city: str
    role: str
    drivers_count: int
    is_verified: bool
    is_active: bool

    #stripe details
    stripe_customer_id: Optional[str]
    stripe_account_id: Optional[str]
    subscription_status: Optional[str]
    subscription_plan: Optional[str]
    total_ride_count: Optional[int]
    daily_ride_count:Optional[int]
    last_ride_count_reset:Optional[datetime]
    
    created_on: datetime
    updated_on: Optional[datetime]
    
    model_config = {
        "from_attributes": True

    }

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
    driver_id: int 

class TenantLogin(BaseModel):
    email: EmailStr
    password: str


