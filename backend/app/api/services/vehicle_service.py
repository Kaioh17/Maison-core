from fastapi import HTTPException, status
from app.models import vehicle,tenant, vehicle_config, vehicle_category_rate
from app.utils import db_error_handler
from app.utils.logging import logger
import json
from pathlib import Path
db_exceptions = db_error_handler.DBErrorHandler


vehicle_category_table = vehicle_category_rate.VehicleCategoryRate
vehicle_config_table = vehicle_config.VehicleConfig

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
    ##automaticlly set tenant id from current user 
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

        user = current_user.id
        if current_user.role != "tenant":
            user = current_user.tenant_id


        new_vehicle = vehicle.Vehicles(tenant_id=user, **vehicle_info)

       
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        await allocate_vehicle_category(payload, db, user, new_vehicle.id)
        logger.info(f"{payload.make} added to {tenants.company}..")
        
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

    return new_vehicle


def load_vehicles():
    vehicle_data = None
    
    path =Path(__file__).parent.parent.parent/ "data"/ "vehicles.json"
    with open(path, "r") as f:
           vehicle_data = json.load(f)
    logger.info("File found and data read!!")
    return vehicle_data
async def allocate_vehicle_category(payload, db, id_tenant, id_vehicle):
    

    vehicle_category = load_vehicles()
    
    
    # if current_tenant.role == driver
    if vehicle_category:
        found = False
        for v in vehicle_category:
            # logger.info(f"{v["make"]}")
            if (v["make"].lower() == payload.make.lower()
            and v["model"].lower() == payload.model.lower()
            and v["year"] == payload.year):
                vehicle_category_rate = db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == id_tenant, 
                                                               vehicle_category_table.vehicle_category == v["category"]).first()
                vehicle_category = vehicle_config.VehicleConfig(vehicle_id = id_vehicle,
                                                                 tenant_id = id_tenant, 
                                                                 vehicle_category = v["category"], 
                                                                seating_capacity = v["seating_capacity"], 
                                                                vehicle_flat_rate = vehicle_category_rate.vehicle_flat_rate)
                
            
                db.add(vehicle_category)
                db.commit()

    
                found = True
                break   
    if not found:
        raise ValueError( "car is not present in data form ")
    
    vehicle_obj = db.query(vehicle.Vehicles).filter(vehicle.Vehicles.id == id_vehicle).first()
    if not vehicle_obj:
        raise HTTPException(status_code=404,
                            detail = "vehicle not found")
    vehicle_obj.vehicle_config_id = vehicle_category.id
    logger.info("Vehicle config updated")
    db.commit()



    return vehicle_category

"""Update vehicle flat rate """
async def set_vehicle_flat_rate(db, payload, current_user):
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