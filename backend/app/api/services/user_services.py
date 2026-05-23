from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
from ..core import deps
from app.models import user, driver, tenant
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from .helper_service import Validations
from .service_context import ServiceContext
from .email_services import riders

from .helper_service import *
db_exceptions = db_error_handler.DBErrorHandler
# user_table = user.Users
# tenant_table = tenant.Tenants

class UserService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db=db, current_user=current_user)
        self.validate = Validations(self.db)
    async def create_user(self, payload, slug):
        try:
            logger.debug(f"new method hit {slug}")
            tenant_id = self.validate._verify_slug(slug=slug)
            exists = self.db.query(user_table).filter(user_table.email == payload.email, 
                                                user_table.tenant_id == tenant_id, 
                                                user_table.phone_no == payload.phone_no
                                                ).first()  
            if exists:
                logger.debug(f"User with {payload.email} already exists")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail= f"User with {payload.email} already exists")    
            
            
            self.validate._tenants_exist(tenant_id=tenant_id)
            self.validate._tenant_activity_(tenant_id=tenant_id)

            hashed_pwd = password_utils.hash(payload.password) #hash password

            #if user exists
        
            user_info = payload.model_dump()
            user_info.pop("tenants", None)
            new_user = user.Users(**user_info)
            new_user.password = hashed_pwd
            new_user.tenant_id = tenant_id
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            logger.debug(f"{type(new_user)}")
            
            # Email: Send welcome email to rider
            tenant_profile_obj = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
            slug = tenant_profile_obj.slug if tenant_profile_obj else None
            if slug:
                op = tenant_profile_obj.company_name if tenant_profile_obj else slug
                riders.RiderEmailServices(
                    to_email=new_user.email,
                    from_email=self.tenant_email if hasattr(self, 'tenant_email') else 'noreply@example.com',
                    operator_name=op,
                ).welcome_email(
                    obj=new_user,
                    slug=slug
                )
            
            return success_resp(msg="Successfull Created user", data=new_user)
            
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)

        # logger.info(f"User {full_name} has been added")

    async def get_user_info(self):
        try:
            logger.info(f"Getting user info for {self.current_user.email}")
            user_info = self.db.query(user.Users).filter(user.Users.email == self.current_user.email).first()
            return success_resp(data=user_info)
            
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
    
    async def rate_it(self, payload):
        try:
            rating = payload.model_dump()
            booking_obj: booking_table = (
                self.db.query(booking_table)
                .filter(
                    booking_table.id == payload.booking_id,
                    booking_table.rider_id == self.rider_id,
                    booking_table.tenant_id == self.tenant_id,
                )
                .first()
            )
            if not booking_obj:
                logger.error('Booking not found')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

            if booking_obj.booking_status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail="You can only rate completed bookings",
                )
            booking_ratings_obj: booking_ratings_table = (
                self.db.query(booking_ratings_table)
                .filter(
                    booking_ratings_table.booking_id == payload.booking_id,
                    
                )
                .first()
            )

            logger.debug(f'Ratinng {payload.review_comment}')            
            if not booking_ratings_obj:
                
                new_rating = booking_ratings_table(rider_id=self.rider_id, tenant_id=self.tenant_id, **rating)
                self.db.add(new_rating)
                self.db.commit()
                self.db.refresh(new_rating)
                data = new_rating
            else:
                allowed_fields = {"rating_value", "review_comment"}
                for field, value in rating.items():
                    if field in allowed_fields:
                        setattr(booking_ratings_obj, field, value)
                self.db.commit()
                data = booking_ratings_obj


            tenant_obj = self.db.query(tenant_table).filter(tenant_table.id == self.tenant_id).first()
            logger.debug('Ratinng hghererere')
            op_name = (
                tenant_obj.profile.company_name
                if tenant_obj and hasattr(tenant_obj, "profile") and tenant_obj.profile
                else self.slug
            )
            riders.RiderEmailServices(
                to_email=self.current_user.email,
                from_email=self.tenant_email,
                operator_name=op_name,
            ).booking_status_update_email(
                booking_obj=booking_obj,
                rider_obj=self.current_user,
                slug=self.slug,
                review_comment=data.review_comment,
            )

            return success_resp(msg='Successfully saved rating',data=data)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
    
def get_user_service(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return UserService(db=db, current_user=current_user)
def get_unauthorized_service(db = Depends(get_base_db)):
    return UserService(db=db, current_user=None)
    