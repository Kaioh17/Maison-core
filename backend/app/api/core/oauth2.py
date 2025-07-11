from fastapi import HTTPException,status
from sqlalchemy.orm import Session 
from sqlalchemy.orm import Session
from fastapi.params import Depends
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config import Settings
from schemas import auth
from db.database import get_db
from models import *

role_table_map = {
    "user": user.Users,
    "Tenant": tenant.Tenants
}

"""JWT generation"""

settings = Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY= settings.secret_key
ALGORITHM= settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES= settings.access_token_expire_minutes

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = str(payload.get("id"))
        role: str = payload.get("role")
        if id is None or role is None:
            raise credentials_exception
        token_data = auth.TokenData(id = id, role = role)
    except JWTError:
        raise credentials_exception
    
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credentials_exception =  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"could not validate credentials in get current user", 
                                          headers={"WWW-Authenticate": "Bearer"})
    token = verify_access_token(token, credentials_exception)

    role = token.role

    if not role:
        print(f"role not present {role}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = "No role")
    table = role_table_map.get(role)

    if not table:
        raise credentials_exception

    user = db.query(table).filter(table.id == token.id).first()

    return user
