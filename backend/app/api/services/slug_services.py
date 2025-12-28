from fastapi import HTTPException, status, Depends
from app.models import driver, vehicle
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from app.models import tenant_setting
from .helper_service import Validations
from sqlalchemy.orm import selectinload
from sqlalchemy import join
from .tenants_service import TenantService
from app.db.database import get_db, get_base_db
from ..core import deps
from .helper_service import *
from .service_context import ServiceContext
class SlugService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db=db, current_user=current_user)
    """profile, stats = (
    session.query(TenantProfile, TenantStats)
    .join(TenantStats, TenantStats.tenant_id == TenantProfile.tenant_id)
    .filter(TenantProfile.tenant_id == tenant_id)
    .one()
)
"""
    def verify_slug(self, slug):
        # query = "select * from tenant_settings"
        # resp = self.db.query(tenant_setting_table).filter(tenant_setting_table.slug == slug).first()
        resp = (self.db.query(tenant_setting_table,tenant_profile, tenant_branding )
                    .join(tenant_profile,tenant_profile.tenant_id == tenant_setting_table.tenant_id)
                    .join(tenant_branding, tenant_branding.tenant_id == tenant_setting_table.tenant_id)
                    .filter(tenant_profile.slug == slug).first())
        if not resp:
            logger.debug("Slug not in db")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slug is not in db")
        settings, profile, branding = resp
        response_dict = {"settings":settings.__dict__, "profile":profile.__dict__, "branding":branding.__dict__}
        return success_resp(msg = "Slug exists", data=response_dict)
    def get_tenant_setup(self):
        tenant_id = self.tenant_id
        response = (self.db.query(tenant_setting_table,tenant_profile, tenant_branding, tenant_pricing )
                    .join(tenant_profile,tenant_profile.tenant_id == tenant_setting_table.tenant_id)
                    .join(tenant_branding, tenant_branding.tenant_id == tenant_setting_table.tenant_id)
                    .join(tenant_pricing, tenant_pricing.tenant_id == tenant_setting_table.tenant_id)                    
                    .filter(tenant_profile.tenant_id == tenant_id).first())
       
        if not response:
            logger.debug("Nothing....")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no data")
        settings, profile, branding, pricing = response
        response_dict = {"settings":settings.__dict__, "profile":profile.__dict__,"branding":branding.__dict__, "pricing":pricing.__dict__}
        # logger.debug(response_dict)
        return success_resp(msg="Tenant Setup Retrieved successfully", 
                            data=response_dict)
def get_slug_service(db=Depends(get_base_db)):
    return SlugService(db=db, current_user=None)

def get_slug_authorized_service(db=Depends(get_db), current_user = Depends(deps.get_current_user)):
    return SlugService(db=db, current_user=current_user)