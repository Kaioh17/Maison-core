from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Request
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db.database import get_db
from ..services import tenants_service
from schemas import auth
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from models import tenant
from ..core.oauth2 import create_access_token, verify_access_token
from utils.password_utils import verify

router = APIRouter(
    prefix = '/login',
    tags = ['authentication']
)   

@router.post('/tenats')

def login( request: Request,
    db: Session = Depends(get_db),
    user_credentials: OAuth2PasswordRequestForm = Depends()):
    
    user_query = db.query(tenant.Tenants).filter(tenant.Tenants.email == user_credentials.username)
    user = user_query.first()
    print(f"user data: {user.email}")
   
   
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    
    if not verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid credentials")
    
    access_token = create_access_token(data = {"id": str(user.id)})

    return {
        "access_token" : access_token,
        "token_type": "bearer"
    }
