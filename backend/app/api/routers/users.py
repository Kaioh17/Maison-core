from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import tenants_service, user_services
from app.schemas import user,driver
from ..core import oauth2
from app.utils.logging import logger

router = APIRouter(
    prefix = "/api/v1/users",
    tags = ['Users']
)   


@router.post("/add", status_code=status.HTTP_201_CREATED, response_model= user.UserResponse)
async def create_user(payload: user.UserCreate,db: Session = Depends(get_db)):

    logger.info("user created")
    user = await user_services.create_user(db, payload)
        
    return user

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user_info(db:Session = Depends(get_db), current_rider = Depends(oauth2.get_current_user)):

    user_info = await user_services.get_user_info(db, current_rider)

    return user_info
##get available bookings available drivers 
#set bookings