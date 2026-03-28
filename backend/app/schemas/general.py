from datetime import datetime
# from encodings.punycode import T
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator, field_validator
from typing import Any, Optional, Generic, TypeVar
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Generic response schema for consistent API responses"""
    success: bool = Field(True, description="Indicates if the operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    meta: Optional[dict] = Field(None, description="Additional metadata")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[Any] =Field(None)
class ListResponse(StandardResponse[list[T]]):
    success: bool = True
    message: Optional[str] = None
    data: list[T] | None
    meta: dict
    
class GlobalValidator(BaseModel):
    @field_validator('first_name', 'last_name', 'middle_name',check_fields=False,mode= 'before')
    @classmethod
    def capiptalize(cls, v):
        # fields_set = self.model_fields_set
        
        if isinstance(v, str):
            return v.strip().capitalize()
        return v
    @model_validator(mode="before")
    @classmethod
    def strip_all_strings(cls, data: Any) -> Any:
        # We only care if the input is a dictionary (JSON/Key-Value)
        if isinstance(data, dict):
            return {
                key: (value.strip() if isinstance(value, str) else value)
                for key, value in data.items()
            }
        return data