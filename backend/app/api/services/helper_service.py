from app.models import * 
from fastapi import HTTPException,status 
from app.utils.logging import logger


# table_map = {
# }

# def user_exist(db):
#     db.query()
#     return 
user_table = user.Users
tenant_table = tenant.Tenants
driver_table = driver.Drivers
booking_table = booking.Bookings

@staticmethod
def _tenants_exist(db, data):
    exists = db.query(tenant_table).filter(tenant_table.id == data.tenant_id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Tenant does not exists")
    return exists
@staticmethod
def _user_exist(db, data):
    exists = db.query(user_table).filter(user_table.email == data.email, 
                                         user_table.tenant_id == data.tenant_id).first()  
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"User with {data.email} already exists")



@staticmethod
def _tenant_activity_(db, data):
    tenants = _tenants_exist(db,data)

    if tenants.is_active is False:
        logger.info(f"Tenant is not active right now")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail= f"Tenant {tenants.company_name} is not currently active")
    
    return tenants

"""
validate ids
check if user exist 
handle errors:
    ensure right user is logged in 
"""