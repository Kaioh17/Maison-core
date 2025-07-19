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
    tags = ["Bookings"]
)

#retrieve all bookings 
#

@router.post("/set", status_code=status.HTTP_201_CREATED,response_model= booking.BookingRespose)
async def BookRide(book_ride: booking.CreateBooking, current_rider =  Depends(oauth2.get_current_user) 
             ,db: Session= Depends(get_db), rider = Depends(is_rider)):

    ride_booked = await booking_services.book_ride(book_ride, db, current_rider)
    return ride_booked


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[booking.BookingRespose])
async def BookRide(current_user =  Depends(oauth2.get_current_user) 
                    ,db: Session= Depends(get_db)):
    
    booked_rides = await booking_services.get_booked_rides(db, current_user)

    return booked_rides

##endpoints:
    ##update
    ##PUT    /bookings/{booking_id}         # ❌ Missing - Update booking
# DELETE /bookings/{booking_id}         # ❌ Missing - Cancel booking
# POST   /bookings/{booking_id}/accept  # ❌ Missing - Driver accepts
# POST   /bookings/{booking_id}/start   # ❌ Missing - Start ride
# POST   /bookings/{booking_id}/complete # ❌ Missing - Complete ride
# GET    /bookings/available            # ❌ Missing - Available rides for drivers

###search endpoint using query parameters to filter through date, times, drivers.