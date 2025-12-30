from datetime import datetime
from uuid import UUID
from fastapi import File, UploadFile
from pydantic import BaseModel, Field, FileUrl
from typing import Optional
from .vehicle_config import VehicleCategoryRateResponse


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
    full_name: str
    completed_rides: int
    is_active: bool
    is_registered: str
    status: Optional[str] = "available"
    phone_no: Optional[str] = Field(None, pattern = r'^\+?[\d\s\-\(\)]+$')  # Make optional for response

    model_config = {
        "from_attributes": True

    }
    
class VehicleCategoryRateResponse(BaseModel):
    vehicle_category: Optional[str]
    vehicle_flat_rate: float

class VehicleResponse(VehicleBase):    
    # from .driver import DriverPublic
    tenant_id: int = Field(exclude=True)
    id: int
    created_on: datetime
    driver: Optional[DriverResponse] = None
    vehicle_category: Optional[VehicleCategoryRateResponse] #revert to not optional after cleaning db
    vehicle_images: Optional[dict]

    model_config = {
        "from_attributes": True

    }

   
# class VehiclePublic(Vehicel):    
#     # from .driver import DriverPublic
#     tenant_id: int = Field(exclude=True)
#     id: int = Field(exclude=True)
#     created_on: datetime
#     driver: Optional[DriverResponse] = None
#     vehicle_category: Optional[VehicleCategoryRateResponse] #revert to not optional after cleaning db
#     vehicle_images: Optional[dict]

#     model_config = {
#         "from_attributes": True

#     }
            
            
# class VehicleImage(BaseModel):
    
    
   