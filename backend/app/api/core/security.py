# from app.db.database import get_db
from fastapi.params import Depends
from fastapi import HTTPException, status
from app.config import Settings
from jose import jwt
from app.utils.logging import logger

# from 
settings = Settings()
SECRET_KEY = settings.secret_key
ALGORITHM= settings.algorithm

# def get_tenant_id():
from . import oauth2
def get_tenant_id_from_token(token : str =  Depends(oauth2.oauth2_scheme)):
        logger.info("retrieving")

        try:
            payload =jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        role = payload.get("role")
        
        if role and role.lower() == "tenant":
            # tenant_id = payload
            return payload.get("id")
        return payload.get("tenant_id")   
    

        