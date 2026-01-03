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
from .helper_service import *
from .service_context import ServiceContext
from .email_services import tenants

db_exceptions = db_error_handler.DBErrorHandler

class TenantSettingsService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db=db, current_user=current_user)

    async def get_tenant_settings(self, config_type):
        logger.debug(f"{config_type.lower()}")
        match config_type.lower():
            case "branding":
                config_query = self.db.query(tenant_branding).filter(tenant_branding.tenant_id == self.tenant_id)
            case "pricing":
                config_query = self.db.query(tenant_pricing).filter(tenant_pricing.tenant_id == self.tenant_id)
                
            case "setting":
                config_query = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == self.tenant_id)
            case "booking":
                config_query = self.db.query(tenant_booking_price).filter(tenant_booking_price.tenant_id == self.tenant_id)
                
            case "all":
                """profile, stats = (
                    session.query(TenantProfile, TenantStats)
                    .join(TenantStats, TenantStats.tenant_id == TenantProfile.tenant_id)
                    .filter(TenantProfile.tenant_id == tenant_id)
                    .one()
                )
                """
              
                rows= (
                    self.db.query(TenantSettings, TenantPricing, TenantBranding, TenantBookingPricing)
                    .join(TenantPricing, TenantPricing.tenant_id == TenantSettings.tenant_id)
                    .join(TenantBranding, TenantBranding.tenant_id == TenantSettings.tenant_id)
                    .outerjoin(TenantBookingPricing, TenantBookingPricing.tenant_id == TenantSettings.tenant_id)                    
                    .filter(TenantSettings.tenant_id == self.tenant_id)
                    .all()
                )
                # extract parent (same for all rows)
                if not rows:
                    return None  # or handle no tenant found

                settings, pricing, branding, _ = rows[0]

                # collect all booking rows
                booking_list = [row[3] for row in rows if row[3] is not None]

                # build dict
                config_dict = {
                    "settings": settings.__dict__,
                    "pricing": pricing.__dict__,
                    "branding": branding.__dict__,
                    "booking": [b.__dict__ for b in booking_list],
                }

                # logger.debug(f"New config {config_dict}")
                # config_dict = {"settings":settings.__dict__, "pricing":pricing.__dict__, "branding":branding.__dict__, "booking":list[booking.__dict__]}
                # logger.debug(f"New config {config_dict}")

        config_obj = config_query.first() if config_type != 'all' else None
        if config_type == 'booking':
            config_obj = config_query.all()
            # logger.debug(f"New config {config_obj}")
        if not config_obj:
            if not config_dict:
                
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail = "Settings not found ")
        logger.debug(f"Config: {config_obj}")
        
        return success_resp(data={f"{config_type.lower()}":config_obj}, msg=f"Tenant {config_type} retrieved successfully") if config_type != 'all' else success_resp(data=config_dict, msg=f"Tenant {config_type} retrieved successfully") 
    

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
        
        if not setting_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail = "Settings not found ")
        data_mapped = setting_obj.__dict__
        logger.debug(data_mapped)
        
        for field, value in payload.dict().items():
            if value == None:                
                value = data_mapped[field] 
            # if payload.config:
            #     setting_obj.config =  payload.config
                
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
        

    async def update_tenant_pricing(self, payload):
        try:
            response = self.db.query(tenant_pricing).filter(tenant_pricing.tenant_id == self.tenant_id).first()
            if not response:
                logger.error("Pricing config not found ")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail = "Pricing config not found ")
          
            data_mapped = response.__dict__
            for k,v in payload.dict().items():
                if v == None:
                    v = data_mapped[k]
                if hasattr(response, k):
                    setattr(response, k, v)
            self.db.commit()
            self.db.refresh(response)
            
            
            return success_resp(msg='Updated Pricing config successfuly', data=response)
        except  db_exceptions.COMMON_DB_ERRORS as d:
            db_exceptions.handle(d, self.db)
    async def update_tenant_branding(self, payload):
        try:
            response = self.db.query(tenant_branding).filter(tenant_branding.tenant_id == self.tenant_id).first()
            if not response:
                logger.error("Branding config not found ")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail = "Branding config not found ")
            if payload.slug:
                stmt = (update(tenant_profile).where(tenant_profile.tenant_id == self.tenant_id).values(slug=payload.slug))
                self.db.execute(stmt)       
            data_mapped = response.__dict__
            for k,v in payload.dict().items():
                if v == None:
                    v = data_mapped[k]
                if hasattr(response, k):
                    setattr(response, k, v)
            self.db.commit()
            self.db.refresh(response)
            
            
            return success_resp(msg='Updated branding config successfuly', data=response)
        except  db_exceptions.COMMON_DB_ERRORS as d:
            db_exceptions.handle(d, self.db)
    async def update_tenant_booking(self,service_type, payload):
        try:
            response = self.db.query(tenant_booking_price).filter(tenant_booking_price.tenant_id == self.tenant_id,
                                                                  tenant_booking_price.service_type == service_type).first()
            if not response:
                logger.error("Booking config not found ")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail = "Branding config not found ")
                
            data_mapped = response.__dict__
            for k,v in payload.dict().items():
                if v == None:
                    v = data_mapped[k]
                if hasattr(response, k):
                    setattr(response, k, v)
            self.db.commit()
            self.db.refresh(response)
            
            
            return success_resp(msg='Updated booking config successfuly', data=response)
        except  db_exceptions.COMMON_DB_ERRORS as d:
            db_exceptions.handle(d, self.db)
    async def update_logo(self, logo = None, favicon = None):
        branding_query = self.db.query(tenant_branding).filter(tenant_branding.tenant_id == self.tenant_id)
        profile_obj = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.tenant_id).first()
        
        branding_obj = branding_query.first()
        slug = branding_obj.slug
        logger.debug(slug)
        
        
        if not branding_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"[{self.tenant_id}] Settings not found for user")
        
        if favicon:
            favicon_url = await SupaS3.upload_to_s3(url=favicon, slug=slug, bucket_name = 'favicon')
            branding_obj.favicon_url = favicon_url
        if logo:
            logo_url = await SupaS3.upload_to_s3(url=logo, slug=slug, bucket_name="logos") 
            branding_obj.logo_url = logo_url      
            profile_obj.logo_url = logo_url

        self.db.commit()
        self.db.refresh(branding_obj)
        
        # Email: Send logo update confirmation to tenant
        tenant_obj = self.db.query(tenant_table).filter(tenant_table.id == self.tenant_id).first()
        if tenant_obj and logo:
            tenants.TenantEmailServices(to_email=tenant_obj.email, from_email=tenant_obj.email).logo_update_confirmation_email(
                tenant_obj=tenant_obj,
                slug=self.slug,
                logo_url=logo_url
            )

        return success_resp(data=branding_obj, msg="Tenant logo updated successfully")

def get_tenant_setting_service(current_user=Depends(deps.get_current_user), db=Depends(get_db)):
    return TenantSettingsService(db=db, current_user=current_user)
