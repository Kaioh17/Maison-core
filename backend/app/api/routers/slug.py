from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..services import driver_service
from ..services.slug_services import get_slug_service, SlugService, get_slug_authorized_service
from app.schemas import driver, booking, general, slug
from ..core import deps
from .dependencies import is_driver
from typing import Optional
from app.utils.logging import logger



router = APIRouter(
    prefix = "/api/v1/slug",
    tags = ["Slug"]
)

@router.get("/{slug}", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[slug.TenantSlugResponse])
async def verify_slug(slug:str, slug_service: SlugService = Depends(get_slug_service)):
    
    slug_ = slug_service.verify_slug(slug)
    return slug_

@router.get("/", status_code=status.HTTP_200_OK, response_model= general.StandardResponse[slug.TenantSetupResponse])
async def verify_slug(slug_service: SlugService = Depends(get_slug_authorized_service)):
    
    slug_ = slug_service.get_tenant_setup()
    return slug_