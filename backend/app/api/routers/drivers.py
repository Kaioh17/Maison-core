from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import driver_service
from app.schemas import driver
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

@router.patch("/register", status_code=status.HTTP_202_ACCEPTED,response_model= driver.DriverResponse)
async def create_driver(payload: driver.DriverCreate, db: Session =  Depends(get_db)):
    logger.info("Updating info....")
    driver = await driver_service.register_driver(payload, db)
    return driver