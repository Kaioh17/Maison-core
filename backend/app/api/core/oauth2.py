
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import Settings
from app.schemas import auth
from app.models import *
from app.utils.logging import logger


role_table_map = {
    "rider": user.Users,
    "tenant": tenant.Tenants,
    "driver": driver.Drivers
}

"""JWT generation"""

settings = Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY= settings.secret_key
ALGORITHM= settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES= settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    logger.info(f"Access token expiration: {expire}")
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(days= REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_refresh_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        id: str = str(payload.get("id"))
        role: str = payload.get("role")
        tenant_id: str = payload.get("tenant_id")
        auto_refresh: bool = payload.get("auto_refresh")
        
        if id is None or role is None:
            raise credentials_exception
            
        token_data = auth.TokenData(id=id, role=role, tenant_id=tenant_id, auto_refresh=auto_refresh)
        return token_data
    except JWTError:
        raise credentials_exception

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        id: str = str(payload.get("id"))
        role: str = payload.get("role")
        tenant_id: str = payload.get("tenant_id")
        
        if id is None or role is None:
            raise credentials_exception
            
        token_data = auth.TokenData(id=id, role=role, tenant_id=tenant_id)
        return token_data
    except JWTError:
        raise credentials_exception
    
    

