from app.models import * 
from fastapi import HTTPException,status 

# table_map = {
# }

# def user_exist(db):
#     db.query()
#     return 
user_table = user.Users
tenant_table = tenant.Tenants
driver_table = driver.Drivers
booking_table = booking.Bookings

def _tenants_exist(db, data):
    exists = db.query(tenant_table).filter(tenant_table.id == data.tenant_id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Tenant does not exists")
    return exists

def _user_exist(db, data):
    exists = db.query(user_table).filter(user_table.email == data.email, user_table.tenant_id == payload.tenant_id).first()  
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"User with {data.email} already exists")
"""task ahead"""

"""
validate ids
check if user exist 
handle errors:
    ensure right user is logged in 
"""