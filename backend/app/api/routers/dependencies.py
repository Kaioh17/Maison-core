from fastapi import Depends, HTTPException, status, Request, Security
from ..core import deps
from app.config import Settings
from app.utils.logging import logger

settings = Settings()

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
    if current_tenant.role.lower() != "tenant":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return current_tenant

def is_driver(current_driver = Depends(deps.get_current_user)):
    if current_driver.role not in ("driver", "tenant"):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return True

def tenant_and_driver_check(tenants = Depends(is_tenants),
                     driver = Depends(is_driver)):
    return tenants, driver

from fastapi.security import APIKeyHeader

"""ensure users exist"""
ENV = settings.environment
API_KEY = settings.api_key
api_key_header = APIKeyHeader(name="X-API-Key")
def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        # logger.debug(f'')
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    
    return key