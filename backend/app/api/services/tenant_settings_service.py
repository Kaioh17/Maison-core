from fastapi import HTTPException, status, Depends
from app.models import driver, vehicle
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from app.models import tenant_setting
from .helper_service import Validations
from sqlalchemy.orm import selectinload
from sqlalchemy import update, insert, select, delete
from .tenants_service import TenantService
from app.db.database import get_db, get_base_db
from ..core import deps
from .helper_service import success_resp , vehicle_table, tenant_setting_table, tenant_profile, tenant_table, SupaS3
from .service_context import ServiceContext
from .email_services import tenants

db_exceptions = db_error_handler.DBErrorHandler

class TenantSettingsService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db=db, current_user=current_user)

    async def get_tenant_settings(self):
        setting_query = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == self.tenant_id)
        setting_obj = setting_query.first()

        if not setting_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail = "Settings not found ")
        
        # return setting_obj
        return success_resp(data=setting_obj, msg="Tenant settings retrieved successfully")
    

    async def update_tenant_settings(self,payload):
        """from sqlalchemy import update

# Assuming 'User' is an ORM mapped class
stmt = (
    update(User)
    .where(User.username == 'old_name')
    .values(username='new_name', email='new_email@example.com')
)

with Session(engine) as session: # Or use an existing session
    session.execute(stmt)
    session.commit()
"""
        setting_query = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == self.tenant_id)
        setting_obj = setting_query.first()
        
        if payload.slug:
            stmt = (update(tenant_profile).where(tenant_profile.tenant_id == self.tenant_id).values(slug=payload.slug))
            self.db.execute(stmt)
        if not setting_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail = "Settings not found ")
        data_mapped = setting_obj.__dict__
        logger.debug(data_mapped)
        for field, value in payload.dict().items():
            if value == None:                
                value = data_mapped[field] 
    
            if hasattr(setting_obj, field):
                setattr(setting_obj, field, value)

        self.db.commit()
        self.db.refresh(setting_obj)
        
        # Email: Send settings change notification to tenant
        tenant_obj = self.db.query(tenant_table).filter(tenant_table.id == self.tenant_id).first()
        if tenant_obj:
            changed_settings = {k: v for k, v in payload.dict().items() if v is not None and hasattr(setting_obj, k)}
            if changed_settings:
                tenants.TenantEmailServices(to_email=tenant_obj.email, from_email=tenant_obj.email).settings_change_email(
                    tenant_obj=tenant_obj,
                    slug=self.slug,
                    changed_settings=changed_settings
                )

        return success_resp(data=setting_obj, msg="Tenant settings updated successfully")
        


    async def update_logo(self, logo):
        setting_query = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == self.tenant_id)
        profile_obj = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.tenant_id).first()
        
        setting_obj = setting_query.first()
        slug = setting_obj.slug
        logger.debug(slug)
        logo_url = await SupaS3.upload_to_s3(url=logo, slug=slug, bucket_name="logos") 
       
        
        if not setting_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"[{self.tenant_id}] Settings not found for user")
        
        setting_obj.logo_url = logo_url
        profile_obj.logo_url = logo_url
        self.db.commit()
        self.db.refresh(setting_obj)
        
        # Email: Send logo update confirmation to tenant
        tenant_obj = self.db.query(tenant_table).filter(tenant_table.id == self.tenant_id).first()
        if tenant_obj:
            tenants.TenantEmailServices(to_email=tenant_obj.email, from_email=tenant_obj.email).logo_update_confirmation_email(
                tenant_obj=tenant_obj,
                slug=self.slug,
                logo_url=logo_url
            )

        return success_resp(data=setting_obj, msg="Tenant logo updated successfully")

def get_tenant_setting_service(current_user=Depends(deps.get_current_user), db=Depends(get_db)):
    return TenantSettingsService(db=db, current_user=current_user)
