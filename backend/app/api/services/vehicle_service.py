from fastapi import HTTPException, status
from models import vehicle
from utils import password_utils

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def add_vehicle(payload, db):
    logger.info("Creating vehicle...")

    vehicle_info = payload.model_dump()
    new_vehicle = vehicle.Vehicles(**vehicle_info)


    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    logger.info("Account created..")
    return new_vehicle
