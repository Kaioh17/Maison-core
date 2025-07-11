from fastapi import HTTPException, status
from models import driver
from utils import password_utils

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def create_driver(payload, db):
    logger.info("Creating account...")
    hashed_pwd = password_utils.hash(payload.password) #hash password

    driver_info = payload.model_dump()
    driver_info.pop("users", None)
    new_driver = driver.Drivers(**driver_info)
    new_driver.password = hashed_pwd

    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    logger.info("Account created..")
    return new_driver

## check available rides 
## acheck earnings

    
    