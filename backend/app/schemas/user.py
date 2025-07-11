from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)
    phone_no: str = Field(..., pattern = r'^\+?[\d\s\-\(\)]+$')
    address: Optional[str] = None
    city:  Optional[str] = None
    state:  Optional[str] = None
    country:  Optional[str] = None
    postal_code:  Optional[str] = None
    tenant_id: UUID
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()
class UserCreate(UserBase):
    password: str = Field(min_length=8)

   
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
class UserResponse(UserBase):
    id:UUID
    role: str
    tier: str
    created_on: datetime
    updated_on: datetime