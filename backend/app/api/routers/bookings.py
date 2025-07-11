from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db.database import get_db
from ..services import driver_service
from schemas import booking
from ..core import oauth2

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


router = APIRouter(
    prefix = "/bookings",
    tags = ["bookings"]
)

#retrieve all bookings 
#