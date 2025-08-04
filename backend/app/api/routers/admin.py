from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from app.schemas import tenant
from ..core import deps
from .dependencies import is_rider
from app.utils.logging import logger
from ..services import admin_services

router = APIRouter(
    prefix = "/api/v1/admin",
    tags = ['admin']
)   

@router.delete("/delete_admin/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(tenant_id: int | None,db: Session = Depends(get_base_db)):
    tenant = await admin_services.delete_admin(db, tenant_id)
    return tenant

@router.get("/all_tenants", status_code=status.HTTP_200_OK, response_model = list[tenant.TenantResponse])
async def get_all_tenants(db: Session = Depends(get_base_db)):
    tenants = await admin_services.get_all_tenants(db)
    return tenants

