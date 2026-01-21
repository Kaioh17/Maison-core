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
from app.schemas.tenant_setting import *
from sqlalchemy.orm.attributes import flag_modified



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
        # logger.debug(data_mapped)
        
        for field, value in payload.dict().items():
            logger.debug(f"{field}")
            logger.debug(f"{value}")
            if field == 'config' and value != None and len(value['booking']['types']) > len(data_mapped['config']['booking']['types']):
                new_type = value['booking']['types']
                # logger.debug(f"{new_type}")
                current_types = [k for k, v in data_mapped['config']['booking']['types'].items()]
                logger.debug(current_types)
                
                for k, v in new_type.items():
                    # logger.debug(f'types {k} :{v}')
                    if k not in current_types:
                        _new_type = k
                        new_type_add = TenantBookingPricing(
                            tenant_id=self.tenant_id,
                            service_type = _new_type,
                            deposit_type = 'percentage',
                            deposit_fee =  0.3
                        )
                        self.db.add(new_type_add)
            
            if value == None:          
                logger.debug(f"I am in None: but i shouldnt be{value}")      
                value = data_mapped[field] 
            # if payload.config:
            #     setting_obj.config =  payload.config
            
           
            
            # if field == 'config':
            #     logger.debug(f"Value {value['booking']['types']}")
            # logger.debug(f"{field}")
            # return
            
                
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
    def _is_airport(self, payload: TenantBookingUpdate, service_type):
        if service_type.lower() != 'airport' and payload.stc_rate or payload.gratuity_rate or payload.meet_and_greet_fee or payload.airport_gate_fee:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                detail=f"This [stc_rate, gratuity_rate, meet_and_greet_fee, airport_gate_fee] types only reserved to airport...")
          
        return
    async def update_tenant_booking(self,service_type, payload: TenantBookingUpdate):
        try:
            self._is_airport(payload=payload, service_type=service_type)
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
    
    
    async def delete_service_type(self, service_type: str):
        try:
            service_type = service_type.lower()
            response  = self.db.query(TenantSettings).filter(TenantSettings.tenant_id == self.tenant_id).first()
            
            if not response:
                logger.error("Tenant setting found!!!")
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant setting found!!!")

            config = response.config

            current_service_types = [k for k in config['booking']['types'].keys()]
            if service_type in ['hourly', 'airport', 'dropoff']:
                logger.error(f"Cannot delete system types!!!")
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"Cannot delete system types!!!")
            if service_type not in current_service_types:
                logger.error(f"Service not found")
                raise HTTPException(404, f"Service not found")
            
            del config['booking']['types'][service_type]
            setattr(response, 'config', config)
     
            flag_modified(response, "config")
        
            self.db.commit()
            self.db.refresh(response)
     
            return 
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
def get_tenant_setting_service(current_user=Depends(deps.get_current_user), db=Depends(get_db)):
    return TenantSettingsService(db=db, current_user=current_user)


"""{
    "success": true,
    "message": "Tenant ConfigTypes.ALL retrieved successfully",
    "meta": null,
    "data": {
        "settings": {
            "rider_tiers_enabled": false,
            "config": {
                "booking": {
                    "allow_guest_bookings": true,
                    "show_vehicle_images": false,
                    "types": {
                        "hourly": {
                            "is_deposit_required": true
                        },
                        "airport": {
                            "is_deposit_required": false
                        },
                        "dropoff": {
                            "is_deposit_required": true
                        },
                        "event_dropoff": {
                            "is_deposit_required": true
                        }
                    }
                },
                "branding": {
                    "button_radius": 8,
                    "font_family": "DM Sans"
                },
                "features": {
                    "vip_profiles": true,
                    "show_loyalty_banner": false
                }
            }
        },
        "pricing": {
            "base_fare": 10.0,
            "per_mile_rate": 10.0,
            "per_minute_rate": 10.0,
            "per_hour_rate": 100.0,
            "cancellation_fee": 0.0,
            "discounts": false
        },
        "branding": {
            "theme": "dark",
            "primary_color": "#831616",
            "secondary_color": "#d31717",
            "accent_color": "#a9c035",
            "favicon_url": "https://bbhtdgtsgjipimdqpixw.supabase.co/storage/v1/object/public/favicon/ridez/ridez_texoc-high-resolution-logo.png",
            "slug": "ridez",
            "email_from_name": null,
            "email_from_address": null,
            "logo_url": "https://bbhtdgtsgjipimdqpixw.supabase.co/storage/v1/object/public/logos/ridez/ridez_texoc-high-resolution-logo.png",
            "enable_branding": false
        },
        "booking": [
            {
                "deposit_fee": 75.0,
                "deposit_type": "flat",
                "service_type": "hourly",
                "updated_on": null
            },
            {
                "deposit_fee": 0.3,
                "deposit_type": "percentage",
                "service_type": "airport",
                "updated_on": null
            },
            {
                "deposit_fee": 0.3,
                "deposit_type": "percentage",
                "service_type": "dropoff",
                "updated_on": "2026-01-02T06:58:04.360999Z"
            },
            {
                "deposit_fee": 0.3,
                "deposit_type": "percentage",
                "service_type": "event_dropoff",
                "updated_on": null
            }
        ]
    },
    "error": null
}"""