from fastapi import HTTPException,status
from sqlalchemy.orm import Session 
from sqlalchemy.orm import Session
from fastapi.params import Depends
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config import Settings
from schemas import auth

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
        id: str = str(payload.get("user_id"))
        if id is None:
            raise credentials_exception
        token_data = auth.TokenData(id = id)
    except JWTError:
        raise credentials_exception
    
    return token_data
