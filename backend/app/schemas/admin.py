from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate

import re

class AdminBase(BaseModel):
    email: EmailStr = Field()
    # phone_no: str = Field(..., pattern = r'^\+?[\d\s\-\(\)]+$')
    first_name: str = Field(..., min_length=1, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)
    

    @field_validator('email')
    def validate_email(cls, v):
        return v.lower()
class CreateAdmin(AdminBase):
    password: str = Field(...)
class AdminResponse(AdminBase):
    pass    
    