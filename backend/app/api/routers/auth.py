from fastapi import APIRouter, HTTPException, FastAPI, Response, status, Request, Depends, Path
# from fastapi.params import Depends

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.core import deps
from ..core.auth_rate_limiter import *

from app.db.database import  get_base_db
from ..services import tenants_service
from app.schemas import auth
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.models import tenant,driver, user
from ..core.oauth2 import create_access_token, verify_access_token, create_refresh_token
from app.utils.password_utils import verify
from app.utils.logging import logger
from app.utils import db_error_handler
from app.api.services.auth_service import AuthService, get_auth_service

db_exceptions = db_error_handler.DBErrorHandler

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

@router.post(
    "/login/{role}",
    summary="Sign in (password grant)",
    description=(
        "Authenticate with **email** (`username` field in the form) and **password**. "
        "The path segment **`role`** selects which table is queried: `tenant`, `driver`, or `rider` "
        "(rider = end customer). "
        "On success, returns an **access token** in the response body and stores a **refresh token** in a cookie "
        "(drivers/riders get refresh tokens suitable for `POST /api/v1/auth/refresh`; tenants use `auto_refresh=false` — "
        "use `POST /api/v1/auth/refresh/manual` if you need cookie refresh for tenant sessions).\n\n"
        "**Request body (application/x-www-form-urlencoded):** `username`, `password` (OAuth2 password flow)."
    ),
    response_description="JSON with `access_token`; also sets `refresh_token` cookie.",
)
def login(
    request: Request,
    role: str = Path(
        ...,
        description="Account type to authenticate against.",
        examples=["tenant", "driver", "rider"],
    ),
    auth_service: AuthService = Depends(get_auth_service),
    user_credentials: OAuth2PasswordRequestForm = Depends(),
):
    response = auth_service.login(
        request=request, user_credentials=user_credentials, role=role
    )
    return response


@router.post(
    "/refresh",
    summary="Refresh access token (cookie, auto-refresh only)",
    description=(
        "Reads the HttpOnly **`refresh_token`** cookie, validates it, and returns a new **`access_token`**. "
        "Requires the refresh payload to have **`auto_refresh: true`** (typically **drivers** and **riders** after login). "
        "**Tenant** logins set `auto_refresh=false`; this endpoint will return **401** for those tokens — "
        "use **`POST /api/v1/auth/refresh/manual`** instead."
    ),
    response_description="JSON with a new `access_token`.",
)
async def refresh_access_token(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
):
    response = await auth_service.refresh_token(request=request)
    return response


@router.post(
    "/refresh/manual",
    summary="Refresh access token (cookie, no auto-refresh gate)",
    description=(
        "Same as **`POST /api/v1/auth/refresh`** but **does not** require `auto_refresh` on the refresh token. "
        "Use when you need to rotate the access token from the **`refresh_token`** cookie for sessions "
        "that were issued with **`auto_refresh: false`** (e.g. tenant), or for manual refresh flows."
    ),
    response_description="JSON with a new `access_token`.",
)
async def manual_refresh_access_token(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
):
    response = await auth_service.manual_refresh_token(request=request)
    return response


@router.post(
    "/logout",
    summary="Sign out",
    description=(
        "Clears the **`refresh_token`** cookie (path `/api`). "
        "Clients should also discard the **access token** from memory on logout."
    ),
    response_description="JSON message confirming logout.",
)
async def logout_session(auth_service: AuthService = Depends(get_auth_service)):
    response = auth_service.logout()
    return response
# @router.post('/tenants')
# def login( request: Request,
#     db: Session = Depends(get_base_db),
#     user_credentials: OAuth2PasswordRequestForm = Depends()):

#     try:

#         logger.info("Tenant Login in....")
        
#         #retrieve client ip
#         client_ip = get_remote_address(request)

#         #check user-specific rate limit
#         attempts_key= check_user_specific_rate_limit(
#             email=user_credentials.username,
#             ip = client_ip,
#             max_attempts=3,
#             window_minutes=5
#         )

#         user_query = db.query(tenant.Tenants).filter(tenant.Tenants.email == user_credentials.username)
#         user = user_query.first()
        
#         password = user_credentials.password.strip()

#         if not user:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid credentials")
#         if not verify(password, user.password):
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid credentials")
        
#         clear_failed_attempts(attempts_key)

#         access_token = create_access_token(data = {"id": str(user.id), "role": user.role,  "tenant_id": str(user.id)})
#         refresh_token = create_refresh_token(data = {"id": str(user.id), "role": user.role,  "tenant_id": str(user.id)})
#         # logger.info(f"refresh token: {refresh_token}")

#         response = JSONResponse(content = {"access_token": access_token})
#         response.set_cookie(
#             key = "refresh_token",
#             value= refresh_token,
#             httponly=True,
#             secure=False, #set to true for production 
#             samesite="lax",
#             max_age=60 * 60 * 24 * 30,
#             path= "/api/v1/login/refresh_tenants"  # Changed from "/api/v1/login/refresh_tenants" to "/api"
#         )
#         # logger.info(f"response: {response}")

#         return response
#     except db_exceptions.COMMON_DB_ERRORS as e:
#         db_exceptions.handle(e, db)
#     # return {
#     #     "access_token" : access_token,
#     #     "token_type": "bearer"
#     # }
    

# @router.post('/driver')
# def login( request: Request,
#     db: Session = Depends(get_base_db),
#     user_credentials: OAuth2PasswordRequestForm = Depends()):
    
#     try:
#         logger.info(f"Driver {user_credentials.username} logged in....")
#         #retrieve client ip
#         client_ip = get_remote_address(request)

#         #check user-specific rate limiting 
#         attempts_key= check_user_specific_rate_limit(
#             email=user_credentials.username,
#             ip = client_ip,
#             max_attempts=3,
#             window_minutes=5
#         )
#         driver_query = db.query(driver.Drivers).filter(driver.Drivers.email == user_credentials.username)
#         drivers = driver_query.first()
#         # print(f"user data: {drivers.email}")
#         password = user_credentials.password.strip()

    
#         if not drivers:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid credentials")
        
#         if not verify(password, drivers.password):
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid credentials")
        
#         clear_failed_attempts(attempts_key)

#         access_token = create_access_token(data = {"id": str(drivers.id), "role": drivers.role , "tenant_id": str(drivers.tenant_id)})
#         refresh_token = create_refresh_token(data = {"id": str(drivers.id), "role": drivers.role , "tenant_id": str(drivers.tenant_id)})
#         logger.info(f"refresh token: {refresh_token}")

#         response = JSONResponse(content = {"access_token": access_token})
#         response.set_cookie(
#             key = "refresh_token",
#             value= refresh_token,
#             httponly=True,
#             secure=False, #set to true for prpoduction 
#             samesite="lax",
#             max_age=60 * 60 * 24 * 30,
#             path= "/api"  # Changed from "/api/v1/login/refresh" to "/api"
#         )

#         # return {"msg": response,
#         #         "token_type": "bearer"}
#         return response
       
#     except db_exceptions.COMMON_DB_ERRORS as e:
#         db_exceptions.handle(e, db)
    
# @router.post('/user')
# def login( request: Request,
#     db: Session = Depends(get_base_db),
#     user_credentials: OAuth2PasswordRequestForm = Depends()):
#     try:
#         logger.info(f"User {user_credentials.username} logged in....")
#         #retrieve client ip
#         client_ip = get_remote_address(request)

#         #check user-specific rate limiting 
#         attempts_key= check_user_specific_rate_limit(
#             email=user_credentials.username,
#             ip = client_ip,
#             max_attempts=3,
#             window_minutes=5
#         )

#         password = user_credentials.password.strip()

#         user_query = db.query(user.Users).filter(user.Users.email == user_credentials.username)
#         users = user_query.first()
#         # print(f"user data: {users.email}")
    
    
#         if not users:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid credentials")
        
#         if not verify(password, users.password):
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid credentials")
#         clear_failed_attempts(attempts_key)
        
#         access_token = create_access_token(data = {"id": str(users.id), "role": users.role, "tenant_id": str(users.tenant_id)})
#         refresh_token = create_refresh_token(data = {"id": str(users.id), "role": users.role, "tenant_id": str(users.tenant_id)})
#         logger.info(f"refresh token: {refresh_token}")

#         response = JSONResponse(content = {"access_token": access_token})
#         response.set_cookie(
#             key = "refresh_token",
#             value= refresh_token,
#             httponly=True,
#             secure=False, #set to true for prpoduction 
#             samesite="lax",
#             max_age=60 * 60 * 24 * 30,
#             path= "/api"  # Changed from "/api/v1/login/refresh" to "/api"
#         )

#         # return {"msg": response,
#         #         # "token_type": "bearer"}
#         return response
#     except db_exceptions.COMMON_DB_ERRORS as e:
#         db_exceptions.handle(e, db)
    

# ###refresh tokens endpoint
# @router.post("/refresh_tenants")
# async def refresh_token(request: Request):
#     try:
#         refresh_token = request.cookies.get("refresh_token")
#         if not refresh_token:
#             logger.error("There is no refresh token...")
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                     detail="No refresh token")
        
#         logger.info("Attempting to refresh tenant token...")
#         credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
#         payload = verify_access_token(refresh_token, credentials_exception)

#         #create new access token
#         logger.info(f"Token refreshed successfully for tenant {payload.id}")
#         token_data = {"id": str(payload.id), "role": payload.role, "tenant_id": str(payload.id)}
#         logger.info(f"Creating new access token with data: {token_data}")
#         new_access_token = create_access_token(data=token_data)
#         logger.info(f"New access token created: {new_access_token[:20]}...")
#         return {"access_token": new_access_token}
#     except Exception as e:
#         logger.error(f"Error refreshing tenant token: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during token refresh")

# # @router.post("/refresh")
# # async def refresh_token(request: Request):
# #     try:
# #         refresh_token = request.cookies.get("refresh_token")
# #         if not refresh_token:
# #             logger.error("There is no refresh token...")
# #             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
# #                                     detail="No refresh token")
        
# #         logger.info("Attempting to refresh token...")
# #         credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
# #         payload = verify_access_token(refresh_token, credentials_exception)

# #         #create new access token
# #         logger.info(f"Token refreshed successfully for user {payload.id}")
# #         token_data = {"id": str(payload.id), "role": payload.role, "tenant_id": str(payload.tenant_id)}
# #         logger.info(f"Creating new access token with data: {token_data}")
# #         new_access_token = create_access_token(data=token_data)
# #         logger.info(f"New access token created: {new_access_token[:20]}...")
# #         return {"access_token": new_access_token}
# #     except Exception as e:
# #         logger.error(f"Error refreshing token: {str(e)}")
# #         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during token refresh")  

# @router.get("/test-auth")
# async def test_auth(current_user = Depends(deps.get_current_user)):
#     """Test endpoint to verify authentication is working"""
#     return {
#         "message": "Authentication successful",
#         "user_id": current_user.id,
#         "role": current_user.role,
#         "email": current_user.email
#     } 