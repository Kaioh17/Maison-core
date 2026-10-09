# from  .service_context import ServiceContext
from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Request, Depends
from fastapi.params import Depends

from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session


from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.core import deps
from ..core.auth_rate_limiter import assert_not_locked, record_failure, clear_failures, hashed
from app.config import Settings

from app.db.database import  get_base_db
from ..core.oauth2 import create_password_reset_token, verify_password_reset_token, PASSWORD_RESET_EXPIRE_MINUTES, create_access_token, verify_access_token, create_refresh_token, verify_refresh_token, revoke_refresh_token
from app.utils.password_utils import verify, hash as hash_password
from app.utils.logging import logger
from app.utils.db_error_handler import DBErrorHandler

# from 
from . import legal_service
from .email_services.password_reset import PasswordResetEmails
from .helper_service import (
    user_table,
    tenant_table,
    driver_table,
    admin_table,
    tenant_profile,
    tenant_branding)

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
    
    RESET_EMAILS_PER_ADDRESS = 3   # reset requests per address / per IP in the window
    RESET_REQUESTS_PER_IP = 10
    RESET_ROLES = {"tenant": tenant_table, "rider": user_table, "driver": driver_table}

    def _reset_table(self, role: str):
        table = self.RESET_ROLES.get(role)
        if table is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request. Role is not valid")
        return table

    def request_password_reset(self, request, role: str, email: str, slug: str | None) -> None:
        """Email a reset link, but only when `email` belongs to an account of that role.

        Riders and drivers are looked up inside the operator named by `slug` and get that operator's
        branded email. Returns nothing either way, so the response cannot be used to find out which
        emails are registered. Requests are counted (not just failures) per address and per IP.
        """
        table = self._reset_table(role)
        email = email.strip().lower()
        slug = (slug or "").strip().lower()
        ip = get_remote_address(request)
        who = hashed(role, slug, email)
        assert_not_locked("pwd_reset", who, self.RESET_EMAILS_PER_ADDRESS)
        assert_not_locked("pwd_reset_ip", ip, self.RESET_REQUESTS_PER_IP)
        record_failure("pwd_reset", who, self.WINDOW_MINUTES)
        record_failure("pwd_reset_ip", ip, self.WINDOW_MINUTES)

        query = self.db.query(table).filter(func.lower(table.email) == email)
        brand = None
        if role != "tenant":
            profile = self.db.query(tenant_profile).filter(tenant_profile.slug == slug).first()
            if not profile:
                logger.info("Password reset requested for an unknown operator slug; nothing sent")
                return
            query = query.filter(table.tenant_id == profile.tenant_id)
            branding = self.db.query(tenant_branding).filter(tenant_branding.tenant_id == profile.tenant_id).first()
            brand = {
                "company_name": profile.company_name,
                "enable_branding": bool(branding and branding.enable_branding),
                "primary_color": branding.primary_color if branding else None,
                "button_text_color": branding.button_text_color if branding else None,
                "logo_url": (branding.logo_url if branding else None) or profile.logo_url,
            }
        user = query.first()
        # Tenants can be deactivated; a driver with no password has not finished onboarding (nothing to reset).
        if not user or not user.password or (role == "tenant" and not user.is_active):
            logger.info(f"Password reset requested for an email that is not a {role} account; nothing sent")
            return
        try:
            PasswordResetEmails(
                to_email=user.email, role=role, first_name=user.full_name,
                token=create_password_reset_token(role, user.id, user.password),
                minutes=PASSWORD_RESET_EXPIRE_MINUTES, slug=slug or None, branding=brand,
            ).send()
        except Exception:
            # Same response whether or not the send worked: a failure here must not reveal the account exists.
            logger.exception("Could not send password reset email")

    def reset_password(self, role: str, token: str, new_password: str) -> None:
        table = self._reset_table(role)
        claims = verify_password_reset_token(token, role)
        user = self.db.query(table).filter(table.id == int(claims["id"])).first()
        if not user or not user.password or (role == "tenant" and not user.is_active):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset link is invalid or has expired.")
        verify_password_reset_token(token, role, user.password)  # single use: the stored hash must still match
        user.password = hash_password(new_password)
        self.db.commit()

    def login(self, request, user_credentials, role:str, legal_version: str | None = None):
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
                logger.debug("Dummy hash entered....")
                verify(password, _DUMMY_HASH)
                fail()
            if not verify(password, user.password):
                logger.debug("Failing actual auth...")
                fail()

            clear_failures("login", account_id)
            if role == 'tenant':
                legal_service.enforce_on_login(self.db, user, request, legal_version)
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
