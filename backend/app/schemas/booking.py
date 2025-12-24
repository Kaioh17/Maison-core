from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, TypeAdapter, field_validator, model_validator
from typing import Optional
import re
from fastapi import HTTPException, status
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, timezone
from .vehicle import VehicleResponse 

class LocationHelper:
    _airport_data = None

    @staticmethod
    def load_airports():
        if LocationHelper._airport_data is None:
            path =Path(__file__).parent.parent/ "data"/ "airports.json"
            with open(path, "r") as f:
                LocationHelper._airport_data = json.load(f)
        return LocationHelper._airport_data
    
    @staticmethod
    def get_airport_for_city(city: str):
        airports = LocationHelper.load_airports()
        return airports.get(city, {"name": f"{city} Airport", "code": "UNK"})
class ServiceType(str, Enum):
    AIRPORT = "airport"
    HOURLY = "hourly"
    DROP_OFF = "dropoff"

class PaymentType(str, Enum):
    CASH = "cash"
    CARD = "card"
    ZELLE = "zelle"

class BoookingBase(BaseModel):
    # driver_id: Optional[int]
    vehicle_id: int = None
    city: str
    service_type: ServiceType
    pickup_location: str
    pickup_time: datetime
    dropoff_location: Optional[str]
    dropoff_time: Optional[datetime]
    payment_method: PaymentType
    notes: Optional[str]

    @field_validator("pickup_time", "dropoff_time")
    def ensure_timezone(cls, value):
        dt = TypeAdapter(datetime).validate_python(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @model_validator(mode = "after")
    def check_dropoff_logic(cls, values):
        service_type = values.service_type
        city = values.city
        dropoff_location = values.dropoff_location

        if service_type.lower() == ServiceType.DROP_OFF and not service_type:
            raise HTTPException(status_code= 400, detail ="A drop off location is required for dropoffs")
        #airport logic
        if service_type.lower() ==ServiceType.AIRPORT:
            airport_info = LocationHelper.get_airport_for_city(city)

            if not dropoff_location:
                setattr(values, 'dropoff_location', airport_info['name'])

        return values

    model_config = {
        "from_attributes": True

    }

class CreateBooking(BoookingBase):

    pass    

class UpdateBookingTenants(BoookingBase):
    pass 
class BookingResponse(BoookingBase):
    id: int
    tenant_id: Optional[int]
    estimated_price: Optional[float]
    booking_status: str
    customer_name: Optional[str] = None
    vehicle: str
    # vehicle_details: Optional[VehicleResponse]
    driver_name: Optional[str] = None
    created_on: Optional[datetime]
    updated_on: Optional[datetime]
   
    @field_validator("driver_name", mode='after')
    def check_empty(cls, value:str):
        if value == " ":
            value = None
            return value
        else: return value