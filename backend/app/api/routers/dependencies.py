from fastapi import Depends, HTTPException, status
from ..core import deps
# from app.api import core
# import core
# from services import helper_service
# from services import helper_service

"""ensure correct-role"""
def is_rider(current_rider = Depends(deps.get_current_user)):
    if current_rider.role != "rider":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return current_rider

def is_tenants(current_tenant = Depends(deps.get_current_user)):
    if current_tenant.role.lower() != "Tenant":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return current_tenant

def is_driver(current_driver = Depends(deps.get_current_user)):
    if current_driver.role != "driver":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return True

def tenant_and_driver_check(tenants = Depends(is_tenants),
                     driver = Depends(is_driver)):
    return tenants, driver
"""ensure users exist"""
