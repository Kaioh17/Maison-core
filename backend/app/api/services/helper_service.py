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

import os
@staticmethod
#this is used to verify uploads from clients and direct to respective directory or s3 bucket 
async def _verify_upload(logo_url,slug: str, upload_dir: str):
    if logo_url:
        try:
            contents = await logo_url.read()
            # Extract filename from the uploaded file
            filename = logo_url.filename if hasattr(logo_url, 'filename') else 'image.jpg'
            os.makedirs(upload_dir, exist_ok=True)
            file_path = f"{upload_dir}/{slug}_{filename}"
            with open(file_path, "wb") as f:
                f.write(contents)
            logger.info(f"{file_path}")
            logger.info("{slug}, image is saved!!")
            return file_path
        except Exception as e:
            logger.warning(f"Failed to save logo upload: {e}")
            # Continue without failing the tenant creation
    return None


"""
validate ids
check if user exist 
handle errors:
    ensure right user is logged in 
"""