from fastapi import HTTPException, status
from app.models import driver, vehicle
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from app.models import tenant_setting
from .helper_service import _tenants_exist
from .vehicle_service import allocate_vehicle_category
from sqlalchemy.orm import selectinload

db_exceptions = db_error_handler.DBErrorHandler
tenant_setting_table= tenant_setting.TenantSettings
vehicle_table = vehicle.Vehicles

async def get_tenant_settings(db, current_tenant):
    setting_query = db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == current_tenant.id)
    setting_obj = setting_query.first()

    if not setting_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Settings not found ")
    
    return setting_obj

async def update_tenant_settings(payload, db, current_tenant):
    setting_query = db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == current_tenant.id)
    setting_obj = setting_query.first()

    if not setting_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Settings not found ")
    for field, value in payload.dict().items():
        setattr(setting_obj, field, value)

    db.commit()
    db.refresh(setting_obj)

    return setting_obj