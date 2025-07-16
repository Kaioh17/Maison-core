from fastapi import HTTPException, status
from app.models import tenant, driver, TenantSettings
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger


db_exceptions = db_error_handler.DBErrorHandler

tenant_table = tenant.Tenants
driver_table = driver.Drivers


def check_unique_fields(model, db, fields: dict):
    try:
        for field_name, value in fields.items():
            column = getattr(model, field_name)
            exists = db.query(model).filter(column == value).first()
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{field_name.replace('_', ' ').title()} already exists"
                )
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
            
def set_up_tenant_settings(new_tenant_id,payload,db):
    try: 
        new_tenants_settings = TenantSettings(tenant_id = new_tenant_id,
                                           logo_url = payload.logo_url, 
                                           slug = payload.slug)
        db.add(new_tenants_settings)
        db.commit()
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)


def create_tenant(db, payload):
    try:
        model_map = {
            "email": payload.email,
            "company_name": payload.company_name,
            "phone_no": payload.phone_no,
            "slug": payload.slug
        }

        check_unique_fields(tenant_table, db, model_map)
        """Create new tenants"""
        hashed_pwd = password_utils.hash(payload.password) #hash password
        tenats_info = payload.model_dump()
        tenats_info.pop("users", None)
        new_tenant = tenant_table(**tenats_info)
        new_tenant.password = hashed_pwd

    
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)
        
        logger.info(f"new tenant_id {new_tenant.id}")
        """add tenants settings"""
        set_up_tenant_settings( new_tenant.id,payload,db)

    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
        
    return new_tenant

def get_company_info(db, current_tenats):
    try: 
        company = db.query(tenant.Tenants).filter(tenant.Tenants.id == current_tenats.id).first()
        if not company:
            logger.warning("404: company is not in db")
            raise HTTPException(status_code=404,
                                detail="Company cannot be found")
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
    return company


async def get_all_drivers(db, current_tenants):
    try:
        logger.info("getting drivers.. ")
        drivers_query = db.query(driver.Drivers).filter(driver.Drivers.tenant_id == current_tenants.id)
        drivers = drivers_query.all()

        if not drivers:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                details = "there are no drivers under this tenants")
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
    return drivers