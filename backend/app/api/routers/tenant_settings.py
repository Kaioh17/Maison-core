from fastapi import APIRouter, HTTPException, FastAPI, Response,status, UploadFile, File
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..services.tenant_settings_service import get_tenant_setting_service, TenantSettingsService
from app.schemas import tenant_setting, general
from ..core import deps
from .dependencies import is_driver
from app.utils.logging import logger
from typing import Optional 


router = APIRouter(
    prefix = "/api/v1/tenant_setting",
    tags = ["tenant_settings"]
)

@router.get("/", status_code=status.HTTP_200_OK, response_model=general.StandardResponse[tenant_setting.TenantResponse])
async def get_tenant_settings(tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service)):
    logger.info("Getting tenant settings")
    tenant_setting_obj = await tenant_settings_service.get_tenant_settings()
    return tenant_setting_obj

@router.patch("/", status_code=status.HTTP_202_ACCEPTED, response_model=general.StandardResponse[tenant_setting.UpdateTenantSetting])
async def update_tenant_settings( payload: tenant_setting.UpdateTenantSetting,
                                 tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service)):
    logger.info("Updating settings...")
    upated_tenant_setting =await tenant_settings_service.update_tenant_settings(payload)
    
    return upated_tenant_setting

@router.patch("/logo", status_code=status.HTTP_202_ACCEPTED, response_model = general.StandardResponse[tenant_setting.updated_vicuals] )
async def update_logo (tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
                       logo_url: Optional[UploadFile] = File(None)):
    
    updated_logo = await tenant_settings_service.update_logo(logo_url)
    return updated_logo