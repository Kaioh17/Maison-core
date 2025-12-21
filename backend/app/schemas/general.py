from datetime import datetime
# from encodings.punycode import T
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator
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