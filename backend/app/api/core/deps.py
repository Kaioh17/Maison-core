##created to prevent cirvcular import
from fastapi import HTTPException,status
from sqlalchemy.orm import Session 
from sqlalchemy.orm import Session
from fastapi.params import Depends
from app.models import *
from . import oauth2
from app.db.database import get_base_db

def get_current_user(token: str = Depends(oauth2.oauth2_scheme), db: Session = Depends(get_base_db)):
    # if db is None:
    #   from app.db.database import get_db
    #   db = next(get_db())
        
    credentials_exception =  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"could not validate credentials in get current user", 
                                          headers={"WWW-Authenticate": "Bearer"})
    token_data = oauth2.verify_access_token(token, credentials_exception)

    role = token_data.role

    if not role:
        print(f"role not present {role}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = "No role")
    table = oauth2.role_table_map.get(role)

    if not table:
        raise credentials_exception

    user = db.query(table).filter(table.id == token_data.id).first()

    return user
