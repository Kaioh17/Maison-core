from datetime import datetime
# from encodings.punycode import T
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, model_validator
from typing import Optional, Generic, TypeVar
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    meta: Optional[dict] = None
    data: Optional[T] = None
class ListResponse(StandardResponse[list[T]]):
    data: list[T] | None
    meta: dict