from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import booking_services
from app.schemas import booking
from ..core import oauth2
from .dependencies import is_rider




router = APIRouter(
    prefix = "/bookings",
    tags = ["bookings"]
)

#retrieve all bookings 
#

@router.post("/set", status_code=status.HTTP_201_CREATED,response_model= booking.BookingRespose)
async def BookRide(book_ride: booking.CreateBooking, current_rider =  Depends(oauth2.get_current_user) 
             ,db: Session= Depends(get_db), rider = Depends(is_rider)):

    ride_booked = await booking_services.book_ride(book_ride, db, current_rider)
    return ride_booked
