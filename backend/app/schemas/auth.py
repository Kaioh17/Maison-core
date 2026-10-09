from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, validator
from typing import Optional
from .tenant import check_password_strength

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None
    role: str
    tenant_id: Optional[str] = None
    auto_refresh: Optional[bool]=None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    slug: Optional[str] = Field(None, description="Operator subdomain; required for riders and drivers.")


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)

    @field_validator('password')
    def validate_password(cls, v):
        return check_password_strength(v)
