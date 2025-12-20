from fastapi import APIRouter, HTTPException, FastAPI, Response,status, UploadFile, File
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..services import tenant_settings_service
from app.schemas import tenant_setting
from ..core import deps
from .dependencies import is_driver
from app.utils.logging import logger
from typing import Optional 
router = APIRouter(
    prefix = "/api/v1/tenant_setting",
    tags = ["tenant_settings"]
)

@router.get("/", status_code=status.HTTP_200_OK, response_model=tenant_setting.TenantResponse)
async def get_tenant_settings(db: Session = Depends(get_db),
                              current_tenant: int = Depends(deps.get_current_user)):
    logger.info("Getting tenant settings")
    tenant_setting_obj = await tenant_settings_service.get_tenant_settings(db, current_tenant)
    return tenant_setting_obj

@router.patch("/", status_code=status.HTTP_202_ACCEPTED, response_model=tenant_setting.UpdateTenantSetting)
async def update_tenant_settings(payload: tenant_setting.UpdateTenantSetting, db: Session = Depends(get_db),
                                 current_tenant: int = Depends(deps.get_current_user)):
    logger.info("Updating settings...")
    upated_tenant_setting =await tenant_settings_service.update_tenant_settings(payload, db, current_tenant)
    
    return upated_tenant_setting

@router.patch("/logo", status_code=status.HTTP_202_ACCEPTED, response_model = tenant_setting.updated_vicuals )
async def update_logo (logo_url: Optional[UploadFile] = File(None), db: Session = Depends(get_db), current_tenant: int = Depends(deps.get_current_user)):
    
    updated_logo = await tenant_settings_service.update_logo(logo_url, db, current_tenant)
    return updated_logo