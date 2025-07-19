from fastapi import HTTPException, status
from app.models import vehicle,tenant
from app.utils import db_error_handler
from app.utils.logging import logger

db_exceptions = db_error_handler.DBErrorHandler

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
        logger.info("Creating vehicle...")

        vehicle_info = payload.model_dump()

        user = current_user.id
        if current_user.role != "tenant":
            user = current_user.tenant_id


        new_vehicle = vehicle.Vehicles(tenant_id=user, **vehicle_info)

        
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        logger.info(f"{payload.name} added to {tenants.company}..")
        
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

    return new_vehicle