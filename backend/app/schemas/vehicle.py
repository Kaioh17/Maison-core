from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from .vehicle_config import VehicleConfigResponse


class VehicleBase(BaseModel):
     
    make: str
    model: str
    year: Optional[int]
    license_plate: Optional[str]
    color: Optional[str]
    status: Optional[str] = "available"

    model_config = {
        "from_attributes": True

    }



class VehicleCreate(VehicleBase):
    pass 

class VehicleResponse(VehicleBase):
    tenant_id: int 
    id: int 
    vehicle_config: VehicleConfigResponse
    created_on: datetime
    updated_on: Optional[datetime]

    model_config = {
        "from_attributes": True

    }
   