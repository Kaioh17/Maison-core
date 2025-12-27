from fastapi import HTTPException, status
from app.models import booking, tenant, driver, vehicle_config, vehicle
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *

from app.models import tenant_setting


db_exceptions = db_error_handler.DBErrorHandler

tenant_table = tenant.Tenants
driver_table = driver.Drivers
vehicle_table = vehicle.Vehicles
booking_table = booking.Bookings
# vehicle_category_table = vehicle_category_rate.VehicleCategoryRate


async def delete_admin(db, tenant_id: int):
    tenant= db.query(tenant_table).filter_by(id=tenant_id).first()
    if not tenant:
        logger.error(f"Tenant {tenant_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = f"Tenant {tenant_id} not found")
    db.delete(tenant)
    db.commit()
    logger.info(f"Tenant {tenant_id} has been deleted")
    return {"msg": f"Tenant {tenant_id} has been deleted"}

async def get_all_tenants(db):
    tenants= db.query(tenant_table).all()

    if not tenants:
        logger.error(f"There are no refistered tenants at the moment..")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = f"There are no refistered tenants at the moment..")
    
    # logger.info("There is a toatal of ")
    return tenants
