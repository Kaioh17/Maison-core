from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class VehicleConfigResponse(BaseModel):
    vehicle_category: Optional[str]
    vehicle_flat_rate: float


class VehicleRate(BaseModel):
    vehicle_category: Optional[str]
    # seating_capacity: int
    vehicle_flat_rate: float

class VehicleConfig(BaseModel):
#     vehicle_category: Optional[str]
#     seating_capacity: int
#     vehicle_flat_rate: float
    pass


class VehicleCategoryRateResponse(BaseModel):
    id: int 
    tenant_id: int
    vehicle_category: Optional[str]
    vehicle_flat_rate: float
    created_on: datetime
    allowed_image_types: list
    updated_on: Optional[datetime]