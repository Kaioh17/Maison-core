from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db.database import get_db
from ..services import tenants_service
from schemas import tenant

router = APIRouter(
    prefix = "/tenant",
    tags = ['tenant']
)   


@router.get('/', status_code= status.HTTP_200_OK)
def tenants(db: Session = Depends(get_db)):
    return {"msg": "tenants are active"}

@router.post('/add', status_code=status.HTTP_201_CREATED, response_model= tenant.TenantResponse)
def create_tenants(payload: tenant.TenantCreate,db: Session = Depends(get_db)):
    tenant = tenants_service.create_tenant(db, payload)
    
    
    return tenant