from typing import Optional
from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import booking_services
from ..services.booking_services import get_booking_service, get_unauthorized_booking_service as unauthorized_service, BookingService
from app.schemas import booking
from app.schemas.general import StandardResponse
from ..core import deps
from .dependencies import is_rider
from app.utils.logging import logger



router = APIRouter(
    prefix = "/api/v1/bookings",
    tags = ["Bookings"]
)

#retrieve all bookings
#  
#
@router.get("/public_test", status_code=status.HTTP_200_OK)
def public_info():
    logger.info("Public test started")
    return {"msg": "test endpoint"}

@router.post("/set", status_code=status.HTTP_201_CREATED,response_model= StandardResponse[booking.BookingResponse])
async def BookRide(book_ride: booking.CreateBooking, booking_service: BookingService = Depends(get_booking_service),current_rider =  Depends(deps.get_current_user) 
             ,db: Session= Depends(get_db), rider = Depends(is_rider)):
    
    # ride_booked = await booking_services.book_ride(book_ride, db, current_rider)
    ride_booked = await booking_service.book_ride(book_ride)
    
    return ride_booked


@router.get("/", status_code=status.HTTP_200_OK, response_model=StandardResponse[list[booking.BookingResponse]])
async def BookRide(booking_id: Optional[int] = None, booking_status: Optional[str] = None, booking_service: BookingService = Depends(get_booking_service)):
    
    booked_rides = await booking_service.get_bookings_by(booking_id=booking_id, booking_status=booking_status)
    return booked_rides




