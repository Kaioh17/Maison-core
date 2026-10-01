import secrets
from fastapi import Depends, HTTPException, status, Request, Security
from ..core import deps, oauth2
from app.config import Settings
from app.utils.logging import logger
from app.db.database import get_db
from app.domain.plans import is_entitled, resolve_status
from app.policies.plan_policy import PlanPolicyError
from app.api.services.helper_service import tenant_profile

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

def is_admin(current_admin = Depends(deps.get_current_user)):
    """Platform admin only. The shared X-API-Key is public (it ships in the web bundle), so it is not auth."""
    if current_admin.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail = "Admin access required")
    return current_admin

def get_onboarding_claims(token: str = Depends(oauth2.oauth2_scheme)):
    """Driver onboarding session from `GET /driver/{slug}/verify` (not a login token)."""
    return oauth2.verify_driver_onboarding_token(token)

def is_driver(current_driver = Depends(deps.get_current_user)):
    if current_driver.role not in ("driver", "tenant"):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "unauthorized user")
    return True

def require_active_subscription(current_tenant = Depends(is_tenants),
                                db = Depends(get_db)):
    """Gate a route on subscription state (402 when not entitled).

    Deliberately does NOT check quotas -- those need live row counts and must
    also cover unauthenticated entrypoints, so they live in the service layer.
    This is the cheap, declarative half: it marks a route as billing-gated and
    fails before any work happens.
    """
    profile = db.query(tenant_profile).filter(
        tenant_profile.tenant_id == current_tenant.id
    ).first()
    sub_status = getattr(profile, "subscription_status", None)
    if not is_entitled(sub_status):
        raise PlanPolicyError(
            f"Your subscription is {resolve_status(sub_status)}. "
            "Reactivate your plan to continue."
        )
    return current_tenant

def tenant_and_driver_check(tenants = Depends(is_tenants),
                     driver = Depends(is_driver)):
    return tenants, driver

from fastapi.security import APIKeyHeader

"""ensure users exist"""
ENV = settings.environment
API_KEY = settings.api_key
api_key_header = APIKeyHeader(name="X-API-Key")
def verify_api_key(key: str = Security(api_key_header)):
    if not secrets.compare_digest(key.encode(), API_KEY.encode()):
        # logger.debug(f'')
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    
    return key