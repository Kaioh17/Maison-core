from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db.database import get_db
from ..services import driver_service
from schemas import driver
from ..core import oauth2

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


router = APIRouter(
    prefix = "/driver",
    tags = ["Drivers"]
)

@router.post("/create", status_code=status.HTTP_201_CREATED,response_model= driver.DriverResponse)
async def create_driver(payload: driver.DriverCreate, db: Session =  Depends(get_db)):
    logger.info("Collecting info....")
    driver = await driver_service.create_driver(payload, db)
    return driver