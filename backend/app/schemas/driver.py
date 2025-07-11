from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class DriverBase(BaseModel):
    tenant_id: UUID
    email: EmailStr
    phone_no: str
    first_name: str
    last_name: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    completed_rides: int
    license_number: Optional[str] = None
    vehicle_id: Optional[UUID] = None
    is_active: bool = True
    status: Optional[str] = "available"

class DriverCreate(DriverBase):
    password: str

    
    # @validator('email')
    # def validate_email(cls, v):
    #     return v.lower()
    
    # @validator('slug')
    # def validate_slug(cls, v):
    #     if not re.match(r'^[a-z0-9-]+$', v):
    #         raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
    #     return v.lower()
    
    # @validator('password')
    # def validate_password(cls, v):
    #     if not re.search(r'[A-Z]', v):
    #         raise ValueError('Password must contain at least one uppercase letter')
    #     if not re.search(r'[a-z]', v):
    #         raise ValueError('Password must contain at least one lowercase letter')
    #     if not re.search(r'\d', v):
    #         raise ValueError('Password must contain at least one number')
    #     return v

class DriverResponse(DriverBase):
    id: UUID
    role: str
    created_on: datetime
    updated_on: Optional[datetime] = None

    class Config:
        orm_mode = True


class DriverLogin(BaseModel):
    email: EmailStr
    password: str