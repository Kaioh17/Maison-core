# from  .service_context import ServiceContext
from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Request, Depends
from fastapi.params import Depends

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.core import deps
from ..core.auth_rate_limiter import assert_not_locked, record_failure, clear_failures, hashed
from app.config import Settings

from app.db.database import  get_base_db
from ..core.oauth2 import create_access_token, verify_access_token, create_refresh_token, verify_refresh_token, revoke_refresh_token
from app.utils.password_utils import verify, hash as hash_password
from app.utils.logging import logger
from app.utils.db_error_handler import DBErrorHandler

# from 
from .helper_service import (
    user_table,
    tenant_table,
    driver_table,
    admin_table)

settings = Settings()
# Verified against when the account does not exist so unknown emails cost the same as wrong passwords.
_DUMMY_HASH = hash_password("not-a-real-password")


class AuthService:
    def __init__(self, db):
        self.db = db
    MAX_ATTEMPTS = 5          # failures per account+IP before a lockout
    MAX_IP_FAILURES = 20      # failures from one IP across all accounts
    WINDOW_MINUTES = 15
    environment = settings.environment
    # ponytail: per-role session length so drivers/riders aren't logged out mid-shift/trip
    REFRESH_DAYS_BY_ROLE = {"driver": 30, "rider": 90}
    
    def login(self, request, user_credentials, role:str):
        try:
            allowed_roles = ['tenant', 'rider', 'driver', 'admin']
            if role not in allowed_roles:
                logger.error(f"Invalid request. Role `{role}`is not valid")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid request. Role is not valid")
            table_dict = {
                "tenant":tenant_table,
                "rider":user_table,
                "driver":driver_table,
                "admin":admin_table
                
                        }
            role = role.strip().lower()
            table = table_dict[role]
            
            logger.info(f"{role} login in....")
            
            #retrieve client ip
            client_ip = get_remote_address(request)

            account_id = hashed(role, user_credentials.username.lower(), client_ip)
            assert_not_locked("login", account_id, self.MAX_ATTEMPTS)
            assert_not_locked("login_ip", client_ip, self.MAX_IP_FAILURES)

            def fail():
                record_failure("login", account_id, self.WINDOW_MINUTES)
                record_failure("login_ip", client_ip, self.WINDOW_MINUTES)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Invalid credentials")

            user = self.db.query(table).filter(table.email == user_credentials.username).first()
            password = user_credentials.password.strip()

            if not user:
                verify(password, _DUMMY_HASH)
                fail()
            if not verify(password, user.password):
                fail()

            clear_failures("login", account_id)
            if role == 'tenant':
                tenant_id = user.id
                auto_refresh = False
            elif role == 'admin':
                tenant_id = "not tennat"
                auto_refresh = False
                
            else:
                tenant_id = user.tenant_id
                auto_refresh = True
                
            refresh_days = self.REFRESH_DAYS_BY_ROLE.get(role, settings.refresh_token_expire_days)

            access_token = create_access_token(data = {"id": str(user.id), "role": user.role,  "tenant_id": str(tenant_id)})
            refresh_token = create_refresh_token(data = {"id": str(user.id), "role": user.role,  "tenant_id": str(tenant_id), "auto_refresh": auto_refresh}, expire_days=refresh_days)


            # logger.info(f"refresh token: {refresh_token}")

            response = JSONResponse(content = {"access_token": access_token})
            secure = self.environment.lower() != 'development'  # fail safe: only plain-http local dev gets a non-Secure cookie
            response.set_cookie(
                key = "refresh_token",
                value= refresh_token,
                httponly=True,
                secure=secure, #set to true for production
                samesite="lax",
                max_age=60 * 60 * 24 * refresh_days,
                path= "/api"  # Changed from "/api/v1/login/refresh_tenants" to "/api"
            )
            
            

            return response
        except DBErrorHandler.COMMON_DB_ERRORS as e:
            DBErrorHandler.handle(e, self.db)
    def logout(self, request):
        revoke_refresh_token(request.cookies.get("refresh_token"))
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
            
            logger.info("Attempting to refresh access token (cookie)...")
            credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
            payload = verify_refresh_token(refresh_token, credentials_exception)
            if not payload.auto_refresh:
                logger.debug("Token is flagged with no auto refresh")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is flagged with no auto refresh")
            #create new access token
            logger.info(f"Token refreshed successfully for user {payload.id}")
            
            token_data = {"id": str(payload.id), "role": payload.role, "tenant_id": str(payload.tenant_id), "auto_refresh":True}
            new_access_token = create_access_token(data=token_data)
            return {"access_token": new_access_token}
        except HTTPException:
            raise
        except DBErrorHandler.COMMON_DB_ERRORS as e:
            DBErrorHandler.handle(e, self.db)
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during token refresh")
    async def manual_refresh_token(self, request):
        try:
            refresh_token = request.cookies.get("refresh_token")
            if not refresh_token:
                logger.error("There is no refresh token...")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="No refresh token")
            
            logger.info("Attempting manual refresh (cookie)...")
            credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
            payload = verify_refresh_token(refresh_token, credentials_exception)

            #create new access token
            logger.info(f"Token refreshed successfully for user {payload.id}")
        
            token_data = {"id": str(payload.id), "role": payload.role, "tenant_id": str(payload.tenant_id),  "auto_refresh":True}
            new_access_token = create_access_token(data=token_data)
            return {"access_token": new_access_token}
        except HTTPException:
            raise
        except DBErrorHandler.COMMON_DB_ERRORS as e:
            DBErrorHandler.handle(e, self.db)
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during token refresh")
def get_auth_service(db=Depends(get_base_db)):
    return AuthService(db)