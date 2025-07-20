from fastapi import HTTPException, status
from app.models import driver, vehicle
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from .helper_service import _tenants_exist
from .vehicle_service import allocate_vehicle_category
from sqlalchemy.orm import selectinload

db_exceptions = db_error_handler.DBErrorHandler
driver_table = driver.Drivers
vehicle_table = vehicle.Vehicles

async def _table_checks_(driver_obj, payload, db):
    if not driver_obj:
        logger.warning("Token entered is incorrect...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail = "Token entered is incorrect...")
        
    if driver_obj.email != payload.email or driver_obj.first_name != payload.first_name or driver_obj.last_name != payload.last_name:
        logger.warning("Information provided does not exist in db")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail = "Data does not exists in db. Check with admin.")

    liscense_exists = db.query(driver_table).filter(driver_table.tenant_id == driver_obj.tenant_id, 
                                                    driver_table.license_number == payload.license_number).first()
    if  liscense_exists:
        logger.warning(f"Driver license already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"Driver with liscence number {payload.license_number} already exists")
    

async def register_driver(payload, db):
    """
    Completes driver registration after initial creation by a tenant.

    This function verifies the driver's token and personal information,
    checks for duplicate license numbers, and updates the driver's record
    with the provided registration details and hashed password. If the driver
    is of type 'outsourced' and vehicle data is provided, it also creates a new
    vehicle entry for the driver after ensuring the vehicle does not already exist.
    """
    try:
        logger.info("Creating account...")

        driver_query = db.query(driver_table)\
                        .options(selectinload(driver_table.vehicle))\
                        .filter(driver_table.driver_token == payload.driver_token)
        driver_obj =driver_query.first()
        
        _table_checks_(driver_obj, payload, db)
        ##registeration starts
        logger.info("registeration started...")

        hashed_pwd = password_utils.hash(payload.password) #hash password
        driver_info = payload.model_dump()
        driver_info.pop("users", None)

    
        for key, value in driver_info.items():
            if isinstance(value, dict):
                if driver_obj.driver_type.lower() != "outsourced":
                    continue
                vehicle_data = payload.vehicle.model_dump()
                await _vehicle_exists(vehicle_data, driver_obj, db)
                new_vehicle = vehicle_table(tenant_id = driver_obj.tenant_id,
                                            driver_id = driver_obj.id,
                                            **vehicle_data)
                db.add(new_vehicle)
                # db.commit()
                db.flush()
                db.refresh(new_vehicle)
                logger.info("Vehicle_config has been created")
                await allocate_vehicle_category(payload.vehicle, db, driver_obj.tenant_id, new_vehicle.id)
                logger.info("Vehicle as been registered...")
                continue
            
            setattr(driver_obj, key, value)

        driver_obj.password = hashed_pwd
        driver_obj.is_registered = "registered"
        driver_obj.vehicle_id = new_vehicle.id


        db.commit()
        db.refresh(driver_obj)
        logger.info("Logger driver succesfully registered")
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
       
    return driver_obj

async def _vehicle_exists(vehicle_data, driver, db):
    vehicle_obj = db.query(vehicle_table).filter(vehicle_table.tenant_id == driver.tenant_id,
                                             vehicle_table.license_plate == vehicle_data["license_plate"])
    vehicle_exist = vehicle_obj.first()

    if vehicle_exist:
        logger.warning("Vehicle exists..")
        raise HTTPException(status_code=409,
                            detail="Vehicle with license plate is present..") 
    
    return vehicle_exist


## check available rides 
## acheck earnings

    
    