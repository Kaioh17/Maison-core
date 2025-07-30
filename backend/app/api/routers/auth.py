from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Request
from fastapi.params import Depends

from sqlalchemy.orm import Session


from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from ..core.auth_rate_limiter import *

from app.db.database import  get_base_db
from ..services import tenants_service
from app.schemas import auth
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.models import tenant,driver, user
from ..core.oauth2 import create_access_token, verify_access_token
from app.utils.password_utils import verify
from app.utils.logging import logger
from app.utils import db_error_handler

db_exceptions = db_error_handler.DBErrorHandler

router = APIRouter(
    prefix = '/api/v1/login',
    tags = ['Authentication']
)   

@router.post('/tenants')
def login( request: Request,
    db: Session = Depends(get_base_db),
    user_credentials: OAuth2PasswordRequestForm = Depends()):

    try:

        logger.info("Login in....")
        
        #retrieve client ip
        client_ip = get_remote_address(request)

        #check user-specific rate limiting 
        attempts_key= check_user_specific_rate_limit(
            email=user_credentials.username,
            ip = client_ip,
            max_attempts=3,
            window_minutes=5
        )

        user_query = db.query(tenant.Tenants).filter(tenant.Tenants.email == user_credentials.username)
        user = user_query.first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid credentials")
        if not verify(user_credentials.password, user.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid credentials")
        
        clear_failed_attempts(attempts_key)

        access_token = create_access_token(data = {"id": str(user.id), "role": user.role})

    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
    return {
        "access_token" : access_token,
        "token_type": "bearer"
    }

@router.post('/driver')
def login( request: Request,
    db: Session = Depends(get_base_db),
    user_credentials: OAuth2PasswordRequestForm = Depends()):
    
    try:
        logger.info(f"Driver {user_credentials.username} logged in....")
        #retrieve client ip
        client_ip = get_remote_address(request)

        #check user-specific rate limiting 
        attempts_key= check_user_specific_rate_limit(
            email=user_credentials.username,
            ip = client_ip,
            max_attempts=3,
            window_minutes=5
        )
        driver_query = db.query(driver.Drivers).filter(driver.Drivers.email == user_credentials.username)
        drivers = driver_query.first()
        # print(f"user data: {drivers.email}")
    
    
        if not drivers:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid credentials")
        
        if not verify(user_credentials.password, drivers.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid credentials")
        
        clear_failed_attempts(attempts_key)

        access_token = create_access_token(data = {"id": str(drivers.id), "role": drivers.role , "tenant_id": str(drivers.tenant_id)})

       
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
    return {
                "access_token" : access_token,
                "token_type": "bearer"
            }
@router.post('/user')
def login( request: Request,
    db: Session = Depends(get_base_db),
    user_credentials: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"User {user_credentials.username} logged in....")
        #retrieve client ip
        client_ip = get_remote_address(request)

        #check user-specific rate limiting 
        attempts_key= check_user_specific_rate_limit(
            email=user_credentials.username,
            ip = client_ip,
            max_attempts=3,
            window_minutes=5
        )

        user_query = db.query(user.Users).filter(user.Users.email == user_credentials.username)
        users = user_query.first()
        # print(f"user data: {users.email}")
    
    
        if not users:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid credentials")
        
        if not verify(user_credentials.password, users.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid credentials")
        clear_failed_attempts(attempts_key)
        
        access_token = create_access_token(data = {"id": str(users.id), "role": users.role, "tenant_id": str(users.tenant_id)})
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
    return {
        "access_token" : access_token,
        "token_type": "bearer"
    }