from fastapi import HTTPException, status, Depends
from app.models import *
from app.utils import password_utils, db_error_handler
from app.db.database import get_db, get_base_db
from ..core import deps, oauth2
from app.utils.logging import logger
from .helper_service import *
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from app.domain.plans import resolve_plan
from app.policies.plan_policy import PlanPolicy
from datetime import timedelta, datetime, timezone
from .vehicle_service import VehicleService
from .service_context import ServiceContext
from .email_services import drivers, tenants, riders
from ..services.stripe_services import checkout

db_exceptions = db_error_handler.DBErrorHandler
# driver_table = driver.Drivers
# vehicle_table = vehicle.Vehicles
# booking_table = booking.Bookings
# tenant_table = tenant.Tenants

class DriverService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db=db, current_user=current_user)
    
    @staticmethod
    def _onboarding_tasks(driver):
        """What the driver still has to finish before the account goes live."""
        tasks = [
            {"key": "profile", "label": "Phone number and licence details", "done": bool(driver.phone_no and driver.license_number)},
            {"key": "password", "label": "Create your password", "done": bool(driver.password)},
        ]
        if (driver.driver_type or "").lower() == "outsourced":
            tasks.append({"key": "vehicle", "label": "Register your vehicle", "done": driver.vehicle is not None})
        return tasks

    def _onboarding_view(self, driver):
        # Hand back what was already collected at application/invite time so the
        # registration form can pre-fill instead of asking for it twice, and so
        # driver_type is presented as already decided rather than re-asked.
        return {
            "tenant_id": driver.tenant_id,
            "first_name": driver.first_name,
            "last_name": driver.last_name,
            "email": driver.email,
            "driver_type": driver.driver_type,
            "tasks": self._onboarding_tasks(driver),
        }

    async def check_token(self, slug, token):
        """Exchange the emailed onboarding code for a short-lived onboarding session.

        The code is only consumed when registration completes. Until then the returned
        `onboarding_token` is what authenticates the driver to the onboarding endpoints.
        """
        try:
            logger.info("Checking token..")
            wrong = HTTPException(status_code=status.HTTP_409_CONFLICT,
                                  detail="Incorrect token entered. try again...")
            token = (token or "").strip()
            # An unapproved application has driver_token == "": it must never match anything.
            if not token:
                raise wrong

            response=self.db.query(tenant_profile).filter(tenant_profile.slug == slug).first()
            if not response:
                raise wrong
            tenant_id = response.tenant_id
            dresponse=self.db.query(driver_table).filter(
                driver_table.driver_token == token,
                driver_table.tenant_id == tenant_id,
                driver_table.is_token == False,
                driver_table.is_registered != "registered",
            ).first()

            if not dresponse:
                logger.error(f"Incorrect token entered. try again...")
                raise wrong

            # Token is (re)issued at approval time for self-serve applications, so expiry
            # must count from there (updated_on) rather than the original application's
            # created_on -- falls back to created_on for the tenant-invite flow, where the
            # row is never touched before this call and updated_on is still null.
            await self._ensure_token_not_expired_(created_on = dresponse.updated_on or dresponse.created_on)

            return success_resp(msg="Token Correct you can now register..", data={
                **self._onboarding_view(dresponse),
                "onboarding_token": oauth2.create_driver_onboarding_token(
                    dresponse.id, tenant_id, dresponse.driver_token
                ),
            })

        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)

    async def _get_onboarding_driver(self, claims):
        """The driver an onboarding session belongs to, or 401 if the session is stale."""
        driver_obj = self.db.query(driver_table)\
            .options(selectinload(driver_table.vehicle))\
            .filter(driver_table.id == claims["driver_id"],
                    driver_table.tenant_id == claims["tenant_id"]).first()
        if (not driver_obj
                or driver_obj.is_token
                or driver_obj.is_registered == "registered"
                or not oauth2.driver_token_matches(claims, driver_obj.driver_token)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Onboarding session expired or invalid. Enter your verification code again.")
        return driver_obj

    async def onboarding_status(self, claims):
        try:
            driver_obj = await self._get_onboarding_driver(claims)
            return success_resp(msg="Onboarding in progress", data=self._onboarding_view(driver_obj))
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)

    async def apply(self, payload, slug):
        """
        Self-serve driver application from the public site: a prospective
        driver requests to join a tenant's fleet before any invite exists.

        Creates an *unapproved* driver row -- `driver_token` is left blank so
        the existing `/driver/{slug}/verify` -> `/driver/register` flow can't
        be reached until a tenant approves the application (see
        TenantService.approve_driver, which fills the token in and emails it).
        Notifies both the applicant and the tenant.
        """
        try:
            tenant_id = Validations(db=self.db)._verify_slug(slug)

            # ponytail: no plan-quota check here (unlike TenantService.onboard_drivers) --
            # a tenant can still only Approve up to what their plan allows in practice,
            # but nothing stops the applications themselves from piling up past that.
            # Add plan_policy.PlanPolicy.assert_can_onboard_driver in approve_driver if
            # abuse becomes a real problem.
            existing = self.db.query(driver_table).filter(
                driver_table.email == payload.email,
                driver_table.tenant_id == tenant_id,
            ).first()
            if existing:
                logger.warning("Driver application already exists for this email")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="An application with this email already exists.")

            driver_info = payload.model_dump()
            new_driver = driver_table(
                tenant_id=tenant_id,
                driver_token="",
                is_registered="pending",
                **driver_info,
            )
            self.db.add(new_driver)
            self.db.commit()
            self.db.refresh(new_driver)

            tenant_row = self.db.query(tenant_table).filter(tenant_table.id == tenant_id).first()

            drivers.DriverEmailServices(
                to_email=new_driver.email, from_email='noreply', display_name=slug
            ).application_received_email(obj=new_driver)

            if tenant_row and tenant_row.email:
                tenants.TenantEmailServices(
                    to_email=tenant_row.email, from_email='noreply', display_name=slug
                ).driver_application_email(tenant_obj=tenant_row, driver_obj=new_driver, slug=slug)

            logger.info("Driver application received")
            return success_resp(msg="Application received", data={"id": new_driver.id})
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)

    def _assert_tenant_can_add_vehicle(self, tenant_id):
        """Apply the vehicle quota for a tenant resolved by id, not by session."""
        profile = self.db.query(tenant_profile).filter(
            tenant_profile.tenant_id == tenant_id
        ).first()
        plan = resolve_plan(getattr(profile, "subscription_plan", None))
        sub_status = getattr(profile, "subscription_status", None)
        current_count = self.db.scalar(
            select(func.count()).where(vehicle_table.tenant_id == tenant_id)
        ) or 0
        PlanPolicy.assert_can_add_vehicle(plan, sub_status, current_count)

    async def register_driver(self, payload, claims):
        """
        Completes driver onboarding. `claims` come from the onboarding session issued by
        `check_token`, so the driver is identified by that session and never by anything
        the caller types (name/email/tenant id are not credentials).

        Completing it sets the password, records profile/licence (and vehicle for
        outsourced drivers), consumes the onboarding code and activates the account.
        """
        try:
            logger.info("Creating account...")

            driver_obj: driver_table = await self._get_onboarding_driver(claims)
            tenant_id = driver_obj.tenant_id

            await self._table_checks_(driver_obj, payload) 
            ##registeration starts
            logger.info("registeration started...")

            hashed_pwd = password_utils.hash(payload.password) #hash password
            driver_info = payload.model_dump()
            logger.debug(f"Driver onboarding for driver {driver_obj.id}")

            # Whitelist: email is the identity and password is hashed below, neither is copied across.
            for k in ("first_name", "last_name", "phone_no", "state", "postal_code", "license_number"):
                setattr(driver_obj, k, driver_info[k])
            
            if driver_obj.driver_type.lower() == "outsourced":
            #    for key, value in driver_info.items():
                if driver_info['vehicle'] != None:
                   
                    logger.debug(f"Vehicle detected")
                    
                    vehicle_data = payload.vehicle.model_dump()
                    
                    logger.debug(f"Vehicle detected")
                    
                    await self._vehicle_exists(vehicle_data, driver_obj)

                    # This route is unauthenticated (the driver has no account
                    # yet), so the plan must be resolved from the driver's
                    # tenant rather than from a current_user. Without this an
                    # outsourced driver's vehicle bypassed the vehicle quota
                    # enforced on POST /vehicles/add.
                    self._assert_tenant_can_add_vehicle(driver_obj.tenant_id)

                    get_category_id = VehicleService(db = self.db, current_user = None)._get_category(driver_info['vehicle']['vehicle_category'],tenant_id= driver_obj.tenant_id)
                    vehicle_data.pop("vehicle_category", None)

                    
                    new_vehicle = vehicle_table(tenant_id = driver_obj.tenant_id,
                                                driver_id = driver_obj.id,
                                                vehicle_category_id = get_category_id,
                                                **vehicle_data)
                                                
                 
                    
                    self.db.add(new_vehicle)
                    self.db.flush()
                    self.db.refresh(new_vehicle)
                    
                    driver_obj.vehicle_id = new_vehicle.id

                    logger.info("Vehicle_config has been created")
                    # await allocate_vehicle_category(payload.vehicle, db, driver_obj.tenant_id, new_vehicle.id)
                    logger.info("Vehicle has been registered")
                    # continue
            
                    # setattr(driver_obj, key, value)
                else:
                    logger.error(f"Driver is {driver_obj.driver_type.lower()} so cannot exist without vehicle!! (┬┬﹏┬┬)")
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Driver is {driver_obj.driver_type.lower()} so cannot exist without vehicle!! (┬┬﹏┬┬)") 
        
            
            
                # driver_obj.license_number = payload.license_number
            ##Add it to the 
            driver_obj.password = hashed_pwd
            driver_obj.is_registered = "registered"
            driver_obj.is_token = True  # onboarding code is single-use
            driver_obj.is_active = True  # all onboarding tasks done
            tenant = self.db.query(tenant_stats).filter(tenant_stats.tenant_id == driver_obj.tenant_id).first()

            tenant_driver = tenant.drivers_count + 1 

            tenant.drivers_count = tenant_driver
            self.db.commit()
            self.db.refresh(driver_obj)
            
            ##send emaill
            drivers.DriverEmailServices(to_email=payload.email, from_email='noreply', display_name=driver_obj.slug).welcome_(obj=driver_obj)
            logger.info("Driver succesfully registered")
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
        
        return driver_obj

    async def _vehicle_exists(self,vehicle_data, driver):
        vehicle_obj = self.db.query(vehicle_table).filter(vehicle_table.tenant_id == driver.tenant_id,
                                                vehicle_table.license_plate == vehicle_data["license_plate"])
        vehicle_exist = vehicle_obj.first()

        if vehicle_exist:
            logger.warning("Vehicle exists..")
            raise HTTPException(status_code=409,
                                detail="Vehicle with license plate is present..") 
        
        return vehicle_exist

    async def get_driver(self):
        try:

            logger.info("Getting driver info..")
            
            driver_query = self.db.query(driver_table).filter(driver_table.tenant_id == self.tenant_id,
                                                        driver_table.id == self.driver_id)  
            driver_obj = driver_query.first()
            
                
            if not driver_obj:
                logger.warning(f"Driver {self.tenant_id} not found")
                raise HTTPException(status_code=404, detail="Driver was not found..")
            return driver_obj
            
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
    ## check available rides 
    ## acheck earnings

    ##Check rides
    
    async def get_bookings(db, current_driver, booking_status):
        try:
            booked_rides = db.query(booking_table).filter(booking_table.driver_id == current_driver.id, 
                                                        booking_table.booking_status == booking_status).all()
            if not booked_rides:
                logger.warning("There are no booked_rides..")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = f"There no '{booking_status}' bookings")    
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, db)
        return booked_rides
    async def _validate_action(self,booking_obj: booking_table, action: str):
        logger.debug(f"Drop off time is  {action}")
        
        arrival_time = booking_obj.dropoff_time
        logger.debug(f"Drop off time is  {arrival_time}")
        time_now = datetime.now(timezone.utc)
        logger.debug(f"Current_time  {time_now}")
        
        # formatted_time = time_now.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        to_local_time = DateTime._to_user_time_zone(dt_utc=time_now)
        logger.debug(f"Current_time_at local  {to_local_time}")
        
        if action == 'completed' and to_local_time < arrival_time:
            logger.debug(f"A ride cannot be completed until user is droped off...")
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, f"A ride cannot be completed until user is droped off [{to_local_time}]")
    ##update booked ride response (driver cannot complete rides before ride drop_off time)
    async def driver_ride_response(self,action, booking_id, approve_action):
        try:
            logger.debug(f"driver chose {action}")
            if approve_action:
                booking_obj = self.db.query(booking_table).filter(booking_table.id == booking_id).first()
                driver:driver_table = self.db.query(driver_table).filter(booking_table.id == booking_id, 
                                                                         driver_table.id == booking_obj.driver_id).first()
                if not booking_obj:
                    logger.warning("There are no booked_rides..")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail = f"There no {booking_id} bookings")   
                if booking_obj.booking_status == "completed":
                    logger.error( f"Ride already {booking_obj.booking_status}. Cannot set to `{action}`")
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                        detail = f"Ride already {booking_obj.booking_status}. Cannot set to `{action}`")
                # if ride.booking_satus == "":
                if action not in ('confirmed', 'cancelled', 'completed', 'delayed'):
                    logger.warning("Invalid action: action should be ('confirm', 'cancelled', 'completed', 'delayed')")
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                        detail= "Invalid action: action should be ('confirm', 'cancelled', 'completed', 'delayed')")
                
                if settings.environment == 'production':
                    await self._validate_action(booking_obj=booking_obj, action=action)
                # return
                old_status = booking_obj.booking_status
                old_payment_status = booking_obj.payment_status
                booking_obj.booking_status = action
                logger.debug(f"UPdated {booking_obj.booking_status}")
                if action == "completed":
                    driver.completed_rides += 1
                if action == 'completed' and old_payment_status == 'deposit_paid': 
                    logger.debug("Checkout statrted")
                    await checkout.BookingCheckout(self.current_user, self.db).checkout_session(booking_obj=booking_obj)
                self.db.commit()
                self.db.refresh(booking_obj)
                
                # Email: Send booking status update to rider
                # from .helper_service import user_table
                rider_obj = self.db.query(user_table).filter(user_table.id == booking_obj.rider_id).first()
                if rider_obj:
                    tenant_profile_obj = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == booking_obj.tenant_id).first()
                    tenant_settings:tenant_setting_table = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == booking_obj.tenant_id).first()
                    feedback_url = tenant_settings.rider_feedback_form
                    slug = tenant_profile_obj.slug if tenant_profile_obj else None
                    if slug:
                        op = tenant_profile_obj.company_name if tenant_profile_obj else slug
                        driver_name = None
                        driver_phone = None
                        if booking_obj.driver_id:
                            drv = (
                                self.db.query(driver_table)
                                .filter(driver_table.id == booking_obj.driver_id)
                                .first()
                            )
                            if drv:
                                driver_name = f"{drv.first_name} {drv.last_name}".strip()
                                driver_phone = drv.phone_no
                        tenant_row = (
                            self.db.query(tenant_table)
                            .filter(tenant_table.id == booking_obj.tenant_id)
                            .first()
                        )
                        tenant_contact_email = tenant_row.email if tenant_row else None
                        tenant_contact_phone = tenant_row.phone_no if tenant_row else None
                        vehicle_info = booking_obj.vehicle.vehicle_name if booking_obj.vehicle else None
                        riders.RiderEmailServices(
                            to_email=rider_obj.email, from_email=self.tenant_email, operator_name=op
                        ).booking_status_update_email(
                            booking_obj=booking_obj,
                            rider_obj=rider_obj,
                            slug=slug,
                            old_status=old_status,
                            feedback_url=feedback_url,
                            driver_name=driver_name,
                            driver_phone=driver_phone,
                            tenant_contact_email=tenant_contact_email,
                            tenant_contact_phone=tenant_contact_phone,
                            vehicle_info=vehicle_info,
                        )
                        # Send cancellation email if status is cancelled
                        if action == 'cancelled':
                            riders.RiderEmailServices(
                                to_email=rider_obj.email, from_email=self.tenant_email, operator_name=op
                            ).booking_cancellation_email(
                                booking_obj=booking_obj,
                                rider_obj=rider_obj,
                                slug=slug,
                                driver_name=driver_name,
                                driver_phone=driver_phone,
                            )
                logger.debug({"booking_id":booking_id,"ride_status": action})
                
                return success_resp(msg="Updated succesfully",data={"booking_id":booking_id,"ride_status": action})
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
        
    async def driver_status(self, is_active:bool):
        try:
            
            obj:driver_table = self.db.query(driver_table).filter(driver_table.tenant_id == self.tenant_id, driver_table.id == self.driver_id).first()
            Validations(db=self.db)._obj_empty(obj = obj)
            
            obj.is_active = is_active
            self.db.commit()
            logger.debug(f"{self.current_user.is_active}")
            
            # Email: Send status change notification to driver
            tenant_profile_obj = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.tenant_id).first()
            slug = tenant_profile_obj.slug if tenant_profile_obj else None
            if slug:
                drivers.DriverEmailServices(to_email=obj.email, from_email='noreply', display_name=slug).status_change_email(
                    obj=obj,
                    is_active=is_active
                )
            
            return success_resp(msg="Status changes", data = {"is_active":obj.is_active})
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(exc=e, db=self.db)
    async def _ensure_token_not_expired_(self, created_on):
        try:     
            now = datetime.now(timezone.utc)
            logger.info(f" current time between {now - created_on} ")
            if now - created_on >  timedelta(minutes=1440):
                logger.info("Token has expired!!")
                raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                            detail="Token has timed out...")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unkown error at token verification as {e}")
            raise HTTPException(status_code=500, detail="Unexpected error")  
    
    
    
    async def _table_checks_(self, driver_obj, payload):
        liscense_exists = self.db.query(driver_table).filter(driver_table.tenant_id == driver_obj.tenant_id,
                                                        driver_table.id != driver_obj.id,
                                                        driver_table.license_number == payload.license_number).first()

        if driver_obj.email.lower() != payload.email.lower():
            logger.warning("Information provided does not match the invited driver")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Data does not exists in db. Check with admin.")
        if liscense_exists:
            logger.warning(f"Driver license already exists")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail= f"Driver with liscence number {payload.license_number} already exists")
def get_driver_service(db = Depends(get_db),current_user=Depends(deps.get_current_user)):
    return DriverService(db=db, current_user=current_user)
def get_unauthorized_driver_service(db = Depends(get_base_db)):
    return DriverService(db=db, current_user=None)   
class RiderDriverService:
    def __init__(self, db, current_user):
        self.db = db
        self.current_user = current_user
    async def get_driver_info(self, driver_id: int = None):
        try:
            if not driver_id:
                driver_query = self.db.query(driver_table).join(driver_table.vehicle, isouter = True).filter(driver_table.tenant_id == self.current_user.tenant_id)
                driver_obj = driver_query.all()
            else:
                driver_query = self.db.query(driver_table).join(driver_table.vehicle, isouter = True).filter(driver_table.tenant_id == self.current_user.tenant_id,
                                                                  driver_table.id == driver_id)
                driver_obj = driver_query.all()
            return success_resp(msg="Driver Retrieved for user", data=driver_obj)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)  

def get_rdriver_service(db = Depends(get_db),current_user=Depends(deps.get_current_user)):
    return RiderDriverService(db=db, current_user=current_user)
def get_unauthorized_rdriver_service(db = Depends(get_db)):
    return RiderDriverService(db=db, current_user=None)   
