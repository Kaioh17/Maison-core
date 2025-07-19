from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class VehicleConfigResponse(BaseModel):
    vehicle_category: str
    vehicle_flat_rate: float
    seating_capacity: int

    
    