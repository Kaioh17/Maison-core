from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
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
    

class VehicleResponse(VehicleBase):
    tenant_id: int 
    id: int 
    created_on: datetime
    updated_on: Optional[datetime]
    vehicle_category_id: Optional[int]  #revert to not optional after cleaning db


    model_config = {
        "from_attributes": True

    }
   