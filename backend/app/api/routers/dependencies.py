from fastapi import Depends, HTTPException, status
from ..core import oauth2

# from services import helper_service
# from services import helper_service


"""ensure correct-role"""
def is_rider(current_rider = Depends(oauth2.get_current_user)):
    if current_rider.role != "rider":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return current_rider

def is_tenants(current_tenant = Depends(oauth2.get_current_user)):
    if current_tenant.role.lower() != "Tenant":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return current_tenant

def is_driver(current_driver = Depends(oauth2.get_current_user)):
    if current_driver.role != "Driver":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return current_driver

def tenant_and_driver_check(tenants = Depends(is_tenants),
                     driver = Depends(is_driver)):
    return tenants, driver
"""ensure users exist"""
