
import hashlib
import uuid
from fastapi import HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import jwt, JWTError
from redis.exceptions import RedisError
from datetime import datetime, timedelta
from app.config import Settings
from app.schemas import auth
from app.models import *
from app.utils.logging import logger
from app.redis_connect import redis_client


role_table_map = {
    "rider": user.Users,
    "tenant": tenant.Tenants,
    "driver": driver.Drivers,
    "admin": Admin,
}

"""JWT generation"""

settings = Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY= settings.secret_key
ALGORITHM= settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES= settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
BOOKING_CONFIRM_TOKEN_EXPIRE_DAYS = 7
DRIVER_ONBOARDING_EXPIRE_MINUTES = 120

# Every JWT we mint carries a `type` so one kind can never be replayed as another
# (e.g. a 90-day refresh token used as a Bearer access token). `exp` is mandatory.
ACCESS, REFRESH, DRIVER_ONBOARDING = "access", "refresh", "driver_onboarding"


def _decode(token: str, token_type: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require_exp": True})
    if payload.get("type") != token_type:
        raise JWTError("wrong token type")
    return payload


def _token_fingerprint(driver_token: str) -> str:
    return hashlib.sha256(driver_token.encode()).hexdigest()[:16]


def create_driver_onboarding_token(driver_id: int, tenant_id: int, driver_token: str) -> str:
    """Short-lived session proving the holder entered the driver's onboarding code.

    Bound to a fingerprint of that code, so re-issuing the code (tenant re-approves the
    driver) invalidates sessions opened with the old one. Carries no `role`, so it can
    never authenticate against a normal route.
    """
    return jwt.encode(
        {
            "type": DRIVER_ONBOARDING,
            "id": str(driver_id),
            "tenant_id": str(tenant_id),
            "tk": _token_fingerprint(driver_token),
            "exp": datetime.utcnow() + timedelta(minutes=DRIVER_ONBOARDING_EXPIRE_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_driver_onboarding_token(token: str) -> dict:
    try:
        payload = _decode(token, DRIVER_ONBOARDING)
        return {"driver_id": int(payload["id"]), "tenant_id": int(payload["tenant_id"]), "tk": payload["tk"]}
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Onboarding session expired or invalid. Enter your verification code again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def driver_token_matches(claims: dict, driver_token: str) -> bool:
    return bool(driver_token) and claims["tk"] == _token_fingerprint(driver_token)


def _refresh_key(jti: str) -> str:
    return f"refresh_token:{jti}"


def revoke_refresh_token(token: str | None) -> None:
    """Server-side logout: forget the refresh token's jti so it can never mint another access token."""
    if not token:
        return
    try:
        claims = jwt.get_unverified_claims(token)
        if claims.get("jti"):
            redis_client.delete(_refresh_key(claims["jti"]))
    except (JWTError, RedisError) as e:
        logger.warning(f"Could not revoke refresh token: {e}")


def create_booking_confirm_token(booking_id: int, tenant_id: int, rider_id: int) -> str:
    to_encode = {
        "booking_id": booking_id,
        "tenant_id": tenant_id,
        "rider_id": rider_id,
        "purpose": "booking_confirm",
    }
    expire = datetime.utcnow() + timedelta(days=BOOKING_CONFIRM_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_booking_confirm_token(token: str) -> dict:
    from fastapi import HTTPException, status

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired confirmation link.",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "booking_confirm":
            raise JWTError("Invalid token purpose")
        booking_id = payload.get("booking_id")
        tenant_id = payload.get("tenant_id")
        rider_id = payload.get("rider_id")
        if booking_id is None or tenant_id is None or rider_id is None:
            raise JWTError("Invalid token payload")
        return {
            "booking_id": int(booking_id),
            "tenant_id": int(tenant_id),
            "rider_id": int(rider_id),
        }
    except JWTError:
        raise credentials_exception


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": ACCESS})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def create_refresh_token(data: dict, expire_days: int = None):
    to_encode = data.copy()

    days = expire_days if expire_days is not None else REFRESH_TOKEN_EXPIRE_DAYS
    expire = datetime.utcnow() + timedelta(days = days)
    jti = uuid.uuid4().hex
    to_encode.update({"exp": expire, "type": REFRESH, "jti": jti})

    # Only a jti that is still in Redis can be exchanged, which is what makes logout real.
    redis_client.setex(_refresh_key(jti), timedelta(days=days), "1")

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str, credentials_exception):
    try:
        payload = _decode(token, REFRESH)
        if not redis_client.exists(_refresh_key(payload.get("jti", ""))):
            raise credentials_exception  # logged out / revoked / predates jti tracking

        id = payload.get("id")
        role: str = payload.get("role")
        tenant_id: str = payload.get("tenant_id")
        auto_refresh: bool = payload.get("auto_refresh")

        if id is None or role is None:
            raise credentials_exception

        return auth.TokenData(id=str(id), role=role, tenant_id=tenant_id, auto_refresh=auto_refresh)
    except (JWTError, RedisError):
        raise credentials_exception

def verify_access_token(token: str, credentials_exception):
    try:
        payload = _decode(token, ACCESS)

        id = payload.get("id")
        role: str = payload.get("role")
        tenant_id: str = payload.get("tenant_id")

        if id is None or role is None:
            raise credentials_exception

        return auth.TokenData(id=str(id), role=role, tenant_id=tenant_id)
    except JWTError:
        raise credentials_exception
    
    

