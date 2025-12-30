from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class VehicleConfigResponse(BaseModel):
    vehicle_category: Optional[str] = Field(None)
    vehicle_flat_rate: float = Field()


class VehicleRate(BaseModel):
    vehicle_category: Optional[str] = Field(None)
    # seating_capacity: int
    vehicle_flat_rate: float = Field()

class VehicleConfig(BaseModel):
#     vehicle_category: Optional[str]
#     seating_capacity: int
#     vehicle_flat_rate: float
    pass


class VehicleCategoryRateResponse(BaseModel):
    id: int = Field()
    tenant_id: int = Field(exclude=True)
    vehicle_category: Optional[str] = Field(None)
    vehicle_flat_rate: float = Field()
    created_on: datetime = Field()
    allowed_image_types: list = Field()
    updated_on: Optional[datetime] = Field(None)