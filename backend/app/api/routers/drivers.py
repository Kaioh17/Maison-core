from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
# from ..services import driver_service
from app.schemas import driver, booking, general
from ..core import deps
from .dependencies import is_driver
from typing import Optional
from app.utils.logging import logger
from ..services.driver_service import DriverService,RiderDriverService,get_driver_service, get_unauthorized_driver_service, get_rdriver_service
from ..services.booking_services import get_booking_service, BookingService
"""

TODO drivers endpoint: 

Driver activity toggle (api/v1/driver/active?is_active=true/false)
Accept ride button refine endpoint 
UPDATE vehicle information (patch api/v1/driver/) 
"""

router = APIRouter(
    prefix = "/api/v1/driver",
    tags = ["Drivers"]
)
@router.patch("/status", status_code=status.HTTP_202_ACCEPTED, response_model=general.StandardResponse[dict])
async def drvier_status(is_active: bool,is_driver: bool = Depends(is_driver),
                     driver_service: DriverService = Depends(get_driver_service)):
    status = await driver_service.driver_status(is_active=is_active)
    return status
@router.get("/{slug}/verify", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[dict])
async def get_driver(slug:str,token:str,driver_service: DriverService = Depends(get_unauthorized_driver_service)):
    logger.info("Driver..")
    token = await driver_service.check_token(slug=slug, token=token)
    return token  
@router.patch("/register", status_code=status.HTTP_202_ACCEPTED,response_model= general.StandardResponse[driver.DriverResponse])
async def register_driver(tenant_id: int, payload: driver.DriverCreate, driver_service: DriverService = Depends(get_unauthorized_driver_service) ,db: Session =  Depends(get_base_db)):
    logger.info("Registration begins....")
    driver = await driver_service.register_driver(payload, tenant_id=tenant_id)
    return general.StandardResponse(
        data=driver,
        message="Driver registered successfully"
    )

@router.get("/info", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[driver.DriverResponse])
async def get_driver(is_driver: bool = Depends(is_driver),
                     driver_service: DriverService = Depends(get_driver_service),
                    ):
    logger.info("Driver..")
    driver = await driver_service.get_driver()
    return general.StandardResponse(
        data=driver,
        message="Driver info recieved successfully"
    )

##rider restricted view
@router.get("/rider/info", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[list[driver.RiderDriverResponse]])
async def get_driver(driver_id: int = None, driver_service: RiderDriverService = Depends(get_rdriver_service),
                    current_driver: int = Depends(deps.get_current_user)):
    logger.info("Rider..")
    driver = await driver_service.get_driver_info(driver_id = driver_id)
    return driver

@router.get("/rides/available", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[list[booking.BookingPublic]])
async def get_bookings_for_driver(is_driver: bool = Depends(is_driver),
                                  booking_status: Optional[str] = None,booking_servcie: BookingService = Depends(get_booking_service)):
    logger.info("Availble rides")
    raise HTTPException(status_code=status.HTTP_410_GONE, detail= "Endpoint deprecated")
    bookings = await booking_servcie.get_bookings_by(booking_status=booking_status)
    return bookings

from ..services.analytics.driver import get_driver_analytics, DriverAnalyticService
@router.get("/booking/analytics", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[booking.BookingAnalyticsresponse])
async def get_booking_annalytics(is_driver: bool = Depends(is_driver),
                                  booking_status: Optional[str] = None,booking_servcie: DriverAnalyticService = Depends(get_driver_analytics)):
    # logger.info("Boking )
    # raise HTTPException(status_code=status.HTTP_410_GONE, detail= "Endpoint deprecated")
    bookings = await booking_servcie.booking_analytics()
    return bookings
@router.get("/upcoming/rides", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[list[booking.BookingPublic]])
async def get_upcoming_rides(is_driver: bool = Depends(is_driver),
                                booking_servcie: BookingService = Depends(get_booking_service)):
    logger.info("Availble rides")
    bookings = await booking_servcie.get_upcoming_rides()
    # raise HTTPException(status_code=status.HTTP_410_GONE, detail= "Endpoint deprecated")
    return bookings
"""Set ride status"""
@router.patch("/ride/{booking_id}/decision", status_code=status.HTTP_202_ACCEPTED, response_model=general.StandardResponse[dict])
async def set_ride_status(booking_id: int, action: str =Query(None, description= "Confirm/Cancelled"), approve_action: bool = False,
                       is_driver: bool =  Depends(is_driver), driver_service: DriverService = Depends(get_driver_service)):
    
    ride_decision = await driver_service.driver_ride_response(action, booking_id, approve_action=approve_action)
    return ride_decision
    return bookings
"""Set ride status"""
@router.patch("/ride/{booking_id}/decision", status_code=status.HTTP_202_ACCEPTED, response_model=general.StandardResponse[dict])
async def set_ride_status(booking_id: int, action: str =Query(None, description= "Confirm/Cancelled"), approve_action: bool = False,
                       is_driver: bool =  Depends(is_driver), driver_service: DriverService = Depends(get_driver_service)):
    
    ride_decision = await driver_service.driver_ride_response(action, booking_id, approve_action=approve_action)
    return ride_decision


"""Set ride status"""
@router.patch("/ride/{booking_id}/decision", status_code=status.HTTP_202_ACCEPTED, response_model=general.StandardResponse[dict])
async def set_ride_status(booking_id: int, action: str =Query(None, description= "Confirm/Cancelled"), approve_action: bool = False,
                       is_driver: bool =  Depends(is_driver), driver_service: DriverService = Depends(get_driver_service)):
    
    ride_decision = await driver_service.driver_ride_response(action, booking_id, approve_action=approve_action)
    return ride_decision