from fastapi import HTTPException, status
from models import tenant, driver
from utils import password_utils
from utils.logging import logger

def create_tenant(db, payload):

    """Create new tenants"""
    hashed_pwd = password_utils.hash(payload.password) #hash password

    tenats_info = payload.model_dump()
    tenats_info.pop("users", None)
    new_tenant = tenant.Tenants(**tenats_info)
    new_tenant.password = hashed_pwd

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return new_tenant
def get_company_info(db, current_tenats):

    company = db.query(tenant.Tenants).filter(tenant.Tenants.id == current_tenats.id).first()

    return company

async def get_all_drivers(db, current_tenants):
    logger.info("getting drivers.. ")
    drivers_query = db.query(driver.Drivers).filter(driver.Drivers.tenant_id == current_tenants.id)
    drivers = drivers_query.all()

    if not drivers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            details = "there are no drivers under this tenants")

    return drivers