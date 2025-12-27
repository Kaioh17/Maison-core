# from  .service_context import ServiceContext
from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Request, Depends
from fastapi.params import Depends

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.core import deps
from ..core.auth_rate_limiter import *

from app.db.database import  get_base_db
from ..core.oauth2 import create_access_token, verify_access_token, create_refresh_token, verify_refresh_token
from app.utils.password_utils import verify
from app.utils.logging import logger
from app.utils.db_error_handler import DBErrorHandler

# from 
from .helper_service import (
    user_table,
    tenant_table,
    driver_table)

class AuthService:
    def __init__(self, db):
        self.db = db
    MAX_ATTEMPTS = 3
    WINDOW_MINUTES=5    
    environment = settings.environment
    
    def login(self, request, user_credentials, role:str):
        try:
            allowed_roles = ['tenant', 'rider', 'driver']
            if role not in allowed_roles:
                logger.error(f"Invalid request. Role `{role}`is not valid")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid request. Role is not valid")
            table_dict = {
                "tenant":tenant_table,
                "rider":user_table,
                "driver":driver_table
                        }
            role = role.strip().lower()
            table = table_dict[role]
            
            logger.info(f"{role} login in....")
            
            #retrieve client ip
            client_ip = get_remote_address(request)

            #check user-specific rate limit
            attempts_key= check_user_specific_rate_limit(
                email=user_credentials.username,
                ip = client_ip,
                max_attempts=self.MAX_ATTEMPTS,
                window_minutes=self.WINDOW_MINUTES
            )

            user_query = self.db.query(table).filter(table.email == user_credentials.username)
            user = user_query.first()
            
            password = user_credentials.password.strip()

            if not user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Invalid credentials")
            if not verify(password, user.password):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Invalid credentials")
            
            clear_failed_attempts(attempts_key)
            if role == 'tenant':
                tenant_id = user.id
                auto_refresh = False
            else:
                tenant_id = user.tenant_id
                auto_refresh = True
                
            access_token = create_access_token(data = {"id": str(user.id), "role": user.role,  "tenant_id": str(tenant_id)})
            refresh_token = create_refresh_token(data = {"id": str(user.id), "role": user.role,  "tenant_id": str(tenant_id), "auto_refresh": auto_refresh})
                
                    
            # logger.info(f"refresh token: {refresh_token}")

            response = JSONResponse(content = {"access_token": access_token})
            secure = True if self.environment == 'production' else False
            response.set_cookie(
                key = "refresh_token",
                value= refresh_token,
                httponly=True,
                secure=secure, #set to true for production 
                samesite="lax",
                max_age=60 * 60 * 24 * 30,
                path= "/api"  # Changed from "/api/v1/login/refresh_tenants" to "/api"
            )
            
            

            return response
        except DBErrorHandler.COMMON_DB_ERRORS as e:
            DBErrorHandler.handle(e, self.db)
    def logout(self):
        logger.debug("Logged out")
        response=JSONResponse(content={'message':'logged out'})
        
        response.delete_cookie(
            key="refresh_token",
            path="/api"
        )
        
        return response
    async def refresh_token(self, request):
        try:
            refresh_token = request.cookies.get("refresh_token")
            if not refresh_token:
                logger.error("There is no refresh token...")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="No refresh token")
            
            logger.info("Attempting to refresh tenant token...")
            credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
            payload = verify_refresh_token(refresh_token, credentials_exception)
            if not payload.auto_refresh:
                logger.debug("Token is flagged with no auto refresh")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is flagged with no auto refresh")
            #create new access token
            logger.info(f"Token refreshed successfully for tenant {payload.id}")
            
            token_data = {"id": str(payload.id), "role": payload.role, "tenant_id": str(payload.tenant_id), "auto_refresh":True}
            logger.info(f"Creating new access token with data: {token_data}")
            new_access_token = create_access_token(data=token_data)
            logger.info(f"New access token created: {new_access_token[:20]}...")
            return {"access_token": new_access_token}
        except Exception as e:
            logger.error(f"Error refreshing tenant token: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during token refresh")
        except DBErrorHandler.COMMON_DB_ERRORS as e:
            DBErrorHandler.handle(e, self.db)
    async def manual_refresh_token(self, request):
        try:
            refresh_token = request.cookies.get("refresh_token")
            if not refresh_token:
                logger.error("There is no refresh token...")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="No refresh token")
            
            logger.info("Attempting to refresh tenant token...")
            credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
            payload = verify_refresh_token(refresh_token, credentials_exception)

            #create new access token
            logger.info(f"Token refreshed successfully for tenant {payload.id}")
        
            token_data = {"id": str(payload.id), "role": payload.role, "tenant_id": str(payload.tenant_id),  "auto_refresh":True}
            logger.info(f"Creating new access token with data: {token_data}")
            new_access_token = create_access_token(data=token_data)
            logger.info(f"New access token created: {new_access_token[:20]}...")
            return {"access_token": new_access_token}
        except Exception as e:
            logger.error(f"Error refreshing tenant token: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during token refresh")
        except DBErrorHandler.COMMON_DB_ERRORS as e:
            DBErrorHandler.handle(e, self.db)
def get_auth_service(db=Depends(get_base_db)):
    return AuthService(db)