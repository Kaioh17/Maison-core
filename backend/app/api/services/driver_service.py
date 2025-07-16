from fastapi import HTTPException, status
from app.models import driver
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger

db_exceptions = db_error_handler.DBErrorHandler

async def create_driver(payload, db):
    try:
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
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

## check available rides 
## acheck earnings

    
    