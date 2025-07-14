from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class VehicleBase(BaseModel):
    tenant_id: UUID
    name: str
    model: str
    year: Optional[int]
    license_plate: Optional[str]
    color: Optional[str]
    seating_capacity: Optional[int]
    status: Optional[str] = "available"

    model_config = {
        "from_attributes": True

    }



class VehicleCreate(VehicleBase):
    pass 

class VehicleResponse(VehicleBase):
    id: UUID
    created_on: datetime
    updated_on: Optional[datetime]

    model_config = {
        "from_attributes": True

    }
   