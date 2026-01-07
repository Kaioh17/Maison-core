from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import tenants_service, user_services
from ..services.user_services import UserService, get_user_service, get_unauthorized_service
from app.schemas import user,driver, general
from app.schemas.general import StandardResponse
from ..core import deps
from app.utils.logging import logger
from ..services.analytics.riders import get_rider_analytics, RiderAnalyticService

router = APIRouter(
    prefix = "/api/v1/users",
    tags = ['Users']
)   


@router.post("/add/{tenant_id}", status_code=status.HTTP_201_CREATED, response_model= StandardResponse[dict])
async def create_user(tenant_id: int, payload: user.UserCreate,user_service: UserService =  Depends(get_unauthorized_service)):

    logger.info("Creating User")
    user = await user_service.create_user(payload, tenant_id)
    logger.debug(f"{user}")
    return user

@router.get("/", status_code=status.HTTP_200_OK, response_model=StandardResponse[user.UserResponse])
async def get_user_info(user_service: UserService =  Depends(get_user_service)):

    user_info = await user_service.get_user_info()

    return user_info
@router.get("/booking/analytics", status_code=status.HTTP_200_OK, response_model=StandardResponse[user.BookingAnalytucsresponse])
async def get_user_info(user_service: RiderAnalyticService =  Depends(get_rider_analytics)):

    user_info = await user_service.booking_analytics()

    return user_info
##get available bookings available drivers 
#set bookings