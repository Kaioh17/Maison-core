from fastapi import HTTPException, status
from app.models import tenant, driver
from app.utils import password_utils
from app.utils.logging import logger

def check_unique_fields(model, db, fields: dict):
    for field_name, value in fields.items():
        column = getattr(model, field_name)
        exists = db.query(model).filter(column == value).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{field_name.replace('_', ' ').title()} already exists"
            )

def create_tenant(db, payload):

    model_map = {
        "email": payload.email,
        "company_name": payload.company_name,
        "phone_no": payload.phone_no
    }

    check_unique_fields(tenant.Tenants, db, model_map)
    """Create new tenants"""
    hashed_pwd = password_utils.hash(payload.password) #hash password
    # _tenats_email = db.query(tenant.Tenants).filter(tenant.Tenants.email == payload.email).first()
    # _tenants_company_name = db.query(tenant.Tenants).filter(tenant.Tenants.company_name == payload.company_name).first()
    # _tenats_phone = db.query(tenant.Tenants).filter(tenant.Tenants.phone_no == payload.phone_no).first()

    # if not _tenants_company_name or not _tenats_email or not _tenats_phone:
    #     raise HTTPException(status_code=status.HTTP_409_CONFLICT,
    #                         detail= "user already exists")
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