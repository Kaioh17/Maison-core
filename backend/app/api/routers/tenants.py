from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import tenants_service
from app.schemas import tenant,driver
from ..core import oauth2
from app.utils.logging import logger

router = APIRouter(
    prefix = "/tenant",
    tags = ['Tenant']
)   


@router.get('/', status_code= status.HTTP_200_OK, response_model= tenant.TenantResponse)
def tenants(db: Session = Depends(get_db), current_tenants: int =  Depends(oauth2.get_current_user) ):

    logger.info("Tenant's info")
    company = tenants_service.get_company_info(db,current_tenants)
    return company

@router.post('/add', status_code=status.HTTP_201_CREATED, response_model= tenant.TenantResponse)
def create_tenants(payload: tenant.TenantCreate,db: Session = Depends(get_db)):

    logger.info("Tenants created")
    tenant = tenants_service.create_tenant(db, payload)
    
    
    return tenant

@router.get('/drivers', status_code= status.HTTP_200_OK, response_model= list[driver.DriverResponse])
async def tenants(db: Session = Depends(get_db), current_tenants: int =  Depends(oauth2.get_current_user) ):

    logger.info("Drivers")
    drivers = await tenants_service.get_all_drivers(db,current_tenants)

    return drivers