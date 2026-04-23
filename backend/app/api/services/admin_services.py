from fastapi import HTTPException, status
from fastapi.params import Depends
from app.models import booking, tenant, driver, vehicle_config, vehicle
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *
from app.db.database import get_db, get_base_db

from app.models import tenant_setting
from app.utils import password_utils
from .email_services import admin
from app.config import Settings
from .service_context import ServiceContext
from .helper_service import *
from ..core import deps

settings = Settings()

db_exceptions = db_error_handler.DBErrorHandler

# tenant_table = tenant.Tenants
# driver_table = driver.Drivers
# vehicle_table = vehicle.Vehicles
# booking_table = booking.Bookings
# vehicle_category_table = vehicle_category_rate.VehicleCategoryRate

class AdminService(ServiceContext):
    def __init__(self, current_user, db):
        super().__init__(db, current_user)
    async def create_admin(self, payload):
        data = payload.model_dump()
        response = self.db.query(admin_table).filter(admin_table.email == payload.email).first()
        if response:
            logger.error(f"Cannot signup with existing email")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot signup with existing email")
        hashed_pwd = password_utils.hash(payload.password) #hash password

        new_admin = admin_table(**data)
        new_admin.password = hashed_pwd
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        logger.info('New admin added')
        return new_admin
    async def delete_tenant(self, tenant_id: int):
        tenant= self.db.query(tenant_table).filter_by(id=tenant_id).first()
        if not tenant:
            logger.error(f"Tenant {tenant_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail = f"Tenant {tenant_id} not found")
        company_name = tenant.profile.company_name if hasattr(tenant, 'profile') and tenant.profile else None
        self.db.delete(tenant)
        self.db.commit()
        logger.info(f"Tenant {tenant_id} has been deleted")
        
        # Email: Notify admin of tenant deletion
        admin.AdminEmailServices(to_email=f'admin@{settings.domain}', from_email='noreply').tenant_deletion_confirmation_email(
            tenant_id=tenant_id,
            company_name=company_name,
            deleted_by='admin'
        )
        
        return {"msg": f"Tenant {tenant_id} has been deleted"}

    async def get_all_tenants(self):
        logger.debug("Getting all tenant info....")
        # TODO: Add more information getting all tenants
        tenants= self.db.query(tenant_table).all()

        if not tenants:
            logger.error(f"There are no refistered tenants at the moment..")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail = f"There are no registered tenants at the moment..")
        
        # logger.info("There is a toatal of ")
        return tenants
    async def override_verfied_pertenant(self):
        """TODO We use this feature to force verified for tenant that actially paid"""
        pass
def get_admin_service(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return AdminService(db = db, current_user=current_user)
def unauthenticated_admin_service(db=Depends(get_base_db)):
    """No JWT: use get_base_db — get_db would require Bearer via get_tenant_id_from_token."""
    return AdminService(db=db, current_user=None)