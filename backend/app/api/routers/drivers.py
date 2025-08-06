from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..services import driver_service
from app.schemas import driver, booking, general
from ..core import deps
from .dependencies import is_driver
from typing import Optional
from app.utils.logging import logger


router = APIRouter(
    prefix = "/api/v1/driver",
    tags = ["Drivers"]
)

@router.patch("/register", status_code=status.HTTP_202_ACCEPTED,response_model= general.StandardResponse[driver.DriverResponse])
async def register_driver(payload: driver.DriverCreate, db: Session =  Depends(get_base_db)):
    logger.info("Registration begins....")
    driver = await driver_service.register_driver(payload, db)
    return general.StandardResponse(
        data=driver,
        message="Driver registered successfully"
    )

@router.get("/info", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[driver.DriverResponse])
async def get_driver(is_driver: bool = Depends(is_driver),
                    db: Session = Depends(get_db), 
                    current_driver: int = Depends(deps.get_current_user)):
    logger.info("Driver..")
    driver = await driver_service.get_driver(db, current_driver)
    return general.StandardResponse(
        data=driver,
        message="Driver info recieved successfully"
    )

@router.get("/rides/available", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[list[booking.BookingRespose]])
async def get_bookings_for_driver(is_driver: bool = Depends(is_driver),
                                  booking_status: Optional[str] = "pending",
                                db: Session = Depends(get_db), 
                                current_driver: int = Depends(deps.get_current_user)):
    logger.info("Availble rides...")
    bookings = await driver_service.get_bookings(db, current_driver, booking_status)
    return general.StandardResponse(
        data=bookings,
        message="Available response.."
    )

"""Set ride status"""
@router.patch("/ride/{booking_id}/decision", status_code=status.HTTP_202_ACCEPTED, response_model=general.StandardResponse[booking.BookingRespose])
async def set_ride_status(booking_id: int, action: str =Query(None, description= "Confirm/Cancelled"),
                       is_driver: bool =  Depends(is_driver),
                       db: Session = Depends(get_db), current_driver: int = Depends(get_base_db)):
    
    ride_decision = await driver_service.driver_ride_response(action, db, current_driver, booking_id)
    return general.StandardResponse(
        data=ride_decision,
        message="Available response.."
    )