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
        examples=["tenant", "driver", "rider", "admin"],
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
