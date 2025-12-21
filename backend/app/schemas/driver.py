from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate

import re

class DriverBase(BaseModel):
    email: EmailStr
    phone_no: str = Field(..., pattern = r'^\+?[\d\s\-\(\)]+$')
    first_name: str = Field(..., min_length=1, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)
    state: Optional[str] = None
    postal_code: Optional[str] = None
    license_number: Optional[str] = None
    

    @field_validator('email')
    def validate_email(cls, v):
        return v.lower()

class DriverCreate(DriverBase):
    driver_token: str 
    password: str
    vehicle: Optional[VehicleCreate] = None #outsourced/contracted type only
    ##for inhouse -- due    
    

    
    @field_validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class DriverResponse(DriverBase):
    id: int
    role: str
    driver_type: str
    completed_rides: int
    is_active: bool = True
    status: Optional[str] = "available"
    created_on: datetime
    updated_on: Optional[datetime] = None
    vehicle: Optional[VehicleResponse] = None
    phone_no: Optional[str] = Field(None, pattern = r'^\+?[\d\s\-\(\)]+$')  # Make optional for response

    model_config = {
        "from_attributes": True

    }
class RiderDriverResponse(BaseModel):
    id: int 
    full_name: str
    driver_type: str
    completed_rides: int
    is_active: bool
    status: str
    vehicle: Optional[VehicleResponse] = None
    phone_no: Optional[str] = Field(None, pattern = r'^\+?[\d\s\-\(\)]+$')
    
       

class DriverLogin(BaseModel):
    email: EmailStr
    password: str