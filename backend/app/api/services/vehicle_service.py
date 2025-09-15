from fastapi import HTTPException, status
from app.models import vehicle,tenant, vehicle_config, vehicle_category_rate
from app.utils import db_error_handler
from app.utils.logging import logger
import json
from pathlib import Path
from .helper_service import _verify_upload
from typing import Optional
db_exceptions = db_error_handler.DBErrorHandler


vehicle_category_table = vehicle_category_rate.VehicleCategoryRate
vehicle_config_table = vehicle_config.VehicleConfig
vehicle_table = vehicle.Vehicles

async def get_vehicles(current_user, db):
    try:
        if current_user.role.lower() == "user" or current_user.role.lower() == "driver":
            vehicles = db.query(vehicle.Vehicles).filter(vehicle.Vehicles.tenant_id == current_user.tenant_id).all()
    
        vehicles = db.query(vehicle.Vehicles).filter(vehicle.Vehicles.tenant_id == current_user.id).all()

        if not vehicles:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                   detail = "There are no vehicles")
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

    return vehicles
async def add_vehicle(payload, current_user, db):
    try:
        tenants = db.query(tenant.Tenants).filter(tenant.Tenants.id == current_user.id).first()
        if not tenants:
            raise HTTPException(status_code=404, detail="Tenants not found")
        
        vehicle_exists = db.query(vehicle.Vehicles).filter(vehicle.Vehicles.license_plate == payload.license_plate).first()
        if vehicle_exists:
            logger.warning("Vehicle with license plate already exists")
            raise HTTPException(status_code=409,
                                detail="Vehicle with liscence plate alredy present")
        logger.info("Creating vehicle...")

        vehicle_info = payload.model_dump()
        
        # config = payload.vehicle_category_id 
        user = current_user.id
        if current_user.role != "tenant":
            user = current_user.tenant_id

        # vehicle_category_ = db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == user,
        #                                                             vehicle_category_table.id == config).first()
        
        get_category_id = get_category(payload.vehicle_category, db,user)
        
        vehicle_info.pop("vehicle_category", None) #except vehicle category
        new_vehicle = vehicle.Vehicles(tenant_id=user,vehicle_category_id = get_category_id ,**vehicle_info)

       
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        logger.info(f"{payload.make} added to {tenants.company}..")
        
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

    return new_vehicle

def get_category( vehicle_category, db, user):
    try:
        
        vehicle_category_ = db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == user,
                                                                    vehicle_category_table.vehicle_category== vehicle_category).first()
        
        if not vehicle_category_:
            raise HTTPException(status_code=400,detail="The vehicle category does not exists")
        logger.info(f"Vehicle_category: {vehicle_category_.id}")
        return  vehicle_category_.id
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
        
def load_vehicles():
    try:
        vehicle_data = None
        
        path =Path(__file__).parent.parent.parent/ "data"/ "vehicles.json"

        if not path.exists():
            logger.error(f"Vehicle data file not found at  {path}")
            raise HTTPException(status_code=500,
                                detail="Vehicle configuration file is missing")
        
        with open(path, "r") as f:
            vehicle_data = json.load(f)
        
        if not vehicle_data:
            logger.error("Vehicle data file is empty")
            raise HTTPException(status_code=500,
                                detail="Vehicle configuration is empty")
        logger.info("Vehic;e data loaded success fully")
        return vehicle_data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in vehicle data file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Invalid vehicle configuration format")
    except IOError as e:
        logger.error(f"Error reading vehicle data file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error reading vehicle configuration") 
    

async def add_vehicle_category(payload, current_tenant, db):
    try:
        logger.info(f"[{current_tenant.id}] add new vehicle category...")
        category_info = payload.model_dump()
        vehicle_category = vehicle_category_table(tenant_id = current_tenant.id, **category_info)

        db.add(vehicle_category)
        db.commit()
        db.refresh(vehicle_category)

        return vehicle_category
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
async def update_vehicle_image(vehicle_id: int,vehicle_image, db, current_user):
    try: 
        
        if current_user.role.lower() == "user" or current_user.role.lower() == "driver":
            slug = db.query(tenant.Tenants).filter(tenant.Tenants.id == current_user.tenant_id,
                                                    ).first().slug
            vehicle = db.query(vehicle_table).filter(
                vehicle_table.tenant_id == current_user.tenant_id,
                vehicle_table.id == vehicle_id
            ).first()
        else:
            vehicle = db.query(vehicle_table).filter(vehicle_table.tenant_id == current_user.id ,
                                                                    vehicle_table.id == vehicle_id
                                                    ).first()
            
            slug = current_user.slug

        if not vehicle:
            # logger.warning(f"[Vehicle Not found] {vehicle_make}-{vehicle_model} cannot be updated")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail = "vehicle does not exists")
        
        # logger.info(f"Vehicle image [{vehicle_make}-{vehicle_model}] has been updated")
        upload_dir = f"app/upload/vehicle_image"
        await _verify_upload(vehicle_image, 
                       slug,
                       upload_dir,
                       file_path = f"{upload_dir}/{slug}/_{vehicle.make}{vehicle.model}")
        return {"msg": "Image saved successfully"}
    except Exception as e:
        logger.error(f"There is an unexpected error {e}")


"""Update vehicle flat rate """
async def set_vehicle_flat_rate(db, payload, current_user):
    try:
        category_ = db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == current_user.id,
                                                            vehicle_category_table.vehicle_category == payload.vehicle_category).first()
        config_ = db.query(vehicle_config_table).filter(vehicle_config_table.tenant_id == current_user.id,
                                                        vehicle_config_table.vehicle_category == payload.vehicle_category).all()

        if config_:
            for v in config_:
                v.vehicle_flat_rate = payload.vehicle_flat_rate
        
        if not category_:
            raise HTTPException(status_code=404, detail= f"There is no vehicle catgory for tenant {current_user.id}")
        
        if payload.vehicle_flat_rate < 0:
            logger.warning("Flat rate entered is lower than 0")
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail=f"Vehicle flat rate cannot be lower than 0")
        category_.vehicle_flat_rate = payload.vehicle_flat_rate

        db.commit()
        db.refresh(category_)

        return category_
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)