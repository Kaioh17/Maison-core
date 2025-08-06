from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from app.schemas import tenant, general
from ..core import deps
from .dependencies import is_rider
from app.utils.logging import logger
from ..services import admin_services

router = APIRouter(
    prefix = "/api/v1/admin",
    tags = ['admin']
)   

@router.delete("/delete/{tenant_id}/tenant", status_code=status.HTTP_204_NO_CONTENT)
async def delete(tenant_id: int | None,db: Session = Depends(get_base_db)):
    tenant = await admin_services.delete_admin(db, tenant_id)
    return tenant

@router.get("/tenants", status_code=status.HTTP_200_OK, response_model = general.StandardResponse[list[tenant.TenantResponse]])
async def get_all_tenants(db: Session = Depends(get_base_db)):
    tenants = await admin_services.get_all_tenants(db)
    return general.StandardResponse(
        message="All tenants retrieved successfully",
        data=tenants,
        meta= {"counts": len(tenants)}
    )

##get analytics and summary 
@router.get("/tenants/analytics")
async def tennats_summary():
    ##return the number of riders
    #return number drivers
    #return active time 
    #return 
    pass