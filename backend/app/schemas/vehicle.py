from datetime import datetime
from uuid import UUID
from fastapi import File, UploadFile
from pydantic import BaseModel, Field, FileUrl
from typing import Optional



class VehicleBase(BaseModel):
     
    make: str
    model: str
    year: Optional[int]
    license_plate: Optional[str]
    color: Optional[str]
    status: Optional[str] = "available"
    seating_capacity: Optional[int]
    model_config = {
        "from_attributes": True

    }



class VehicleCreate(VehicleBase):
    vehicle_category: str 
    
class ImageTypes(BaseModel):
    allowed_image_types: list
class DriverResponse(BaseModel):
    id: int
    role: str
    full_name: str
    driver_type: str
    completed_rides: int
    is_active: bool
    is_registered: str
    status: Optional[str] = "available"
    phone_no: Optional[str] = Field(None, pattern = r'^\+?[\d\s\-\(\)]+$')  # Make optional for response
    created_on: datetime
    updated_on: Optional[datetime] = None

    model_config = {
        "from_attributes": True

    }
class VehicleResponse(VehicleBase):
    # from .driver import DriverResponse
    
    tenant_id: int 
    id: int 
    created_on: datetime
    driver: Optional[DriverResponse] = None
    updated_on: Optional[datetime]
    vehicle_category_id: Optional[int]  #revert to not optional after cleaning db
    vehicle_images: Optional[dict]

    model_config = {
        "from_attributes": True

    }
    
# class VehicleImage(BaseModel):
    
    
   