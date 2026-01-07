from fastapi import HTTPException, status, Depends
from app.models import *
from app.utils import password_utils, db_error_handler
from app.db.database import get_db, get_base_db
from ..core import deps
from app.utils.logging import logger
from .helper_service import *
from sqlalchemy.orm import selectinload
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
    
    async def check_token(self, slug, token):
        try:
            logger.info("Checking token..")
            
            response=self.db.query(tenant_profile).filter(tenant_profile.slug == slug).first()
            tenant_id = response.tenant_id
            dresponse=self.db.query(driver_table).filter(driver_table.driver_token == token, driver_table.tenant_id == tenant_id, driver_table.updated_on == None).first()
            
            if not dresponse:
                logger.error(f"Incorrect token entered. try again...")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail = "Incorrect token entered. try again...")
                
            await self._ensure_token_not_expired_(created_on = dresponse.created_on) #check token
            
            dresponse.is_token = True
            self.db.commit()
            return success_resp(msg="Token Correct you can now register..", data={"tenant_id":tenant_id})
        
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db) 
        
    async def register_driver(self,payload,tenant_id):
        """
        Completes driver registration after initial creation by a tenant.

        This function verifies the driver's token and personal information,
        checks for duplicate license numbers, and updates the driver's record
        with the provided registration details and hashed password. If the driver
        is of type 'outsourced' and vehicle data is provided, it also creates a new
        vehicle entry for the driver after ensuring the vehicle does not already exist.
        """
        try:
            logger.info("Creating account...")

            driver_query = self.db.query(driver_table)\
                            .options(selectinload(driver_table.vehicle))\
                            .filter(driver_table.first_name == payload.first_name,
                                    driver_table.last_name == payload.last_name,
                                    driver_table.email == payload.email,
                                    driver_table.tenant_id == tenant_id)
            driver_obj: driver_table =driver_query.first()
            
                
            await self._table_checks_(driver_obj, payload) 
            ##registeration starts
            logger.info("registeration started...")

            hashed_pwd = password_utils.hash(payload.password) #hash password
            driver_info = payload.model_dump()
            driver_info.pop("users", None)
            logger.debug(f"Driver info {driver_info}")
            
            for k, v in driver_info.items():
                
                if k =='vehicle':
                    continue
                    
                setattr(driver_obj, k, v)
            
            if driver_obj.driver_type.lower() == "outsourced":
            #    for key, value in driver_info.items():
                if driver_info['vehicle'] != None:
                   
                    logger.debug(f"Vehicle detected")
                    
                    vehicle_data = payload.vehicle.model_dump()
                    
                    logger.debug(f"Vehicle detected")
                    
                    await self._vehicle_exists(vehicle_data, driver_obj)
                    
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
            tenant = self.db.query(tenant_stats).filter(tenant_stats.tenant_id == driver_obj.tenant_id).first()

            tenant_driver = tenant.drivers_count + 1 

            tenant.drivers_count = tenant_driver
            self.db.commit()
            self.db.refresh(driver_obj)
            
            ##send emaill
            drivers.DriverEmailServices(to_email=payload.email, from_email=driver_obj.tenants.email).welcome_(obj=driver_obj)
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
                    slug = tenant_profile_obj.slug if tenant_profile_obj else None
                    if slug:
                        riders.RiderEmailServices(to_email=rider_obj.email, from_email=self.tenant_email).booking_status_update_email(
                            booking_obj=booking_obj,
                            rider_obj=rider_obj,
                            slug=slug,
                            old_status=old_status
                        )
                        # Send cancellation email if status is cancelled
                        if action == 'cancelled':
                            riders.RiderEmailServices(to_email=rider_obj.email, from_email=self.tenant_email).booking_cancellation_email(
                                booking_obj=booking_obj,
                                rider_obj=rider_obj,
                                slug=slug
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
                drivers.DriverEmailServices(to_email=obj.email, from_email=self.tenant_email).status_change_email(
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
        except Exception as e:
            logger.error(f"Unkown error at token verification as {e}")
            raise HTTPException(status_code=500, detail="Unexpected error")  
    
    
    
    async def _table_checks_(self, driver_obj, payload):
        if not driver_obj:
            logger.warning(f"Data entered is not already registered... ")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail = "Data entered is not already registered...")
        liscense_exists = self.db.query(driver_table).filter(driver_table.tenant_id == driver_obj.tenant_id, 
                                                        driver_table.license_number == payload.license_number).first()
        
        if driver_table.is_token == True:
            logger.warning(f"Token is not approved id:{driver_table.id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail = f"Token is not approved id:{driver_table.id}")
        # elif driver_obj.driver_token != payload.driver_token:

        #         logger.error(f"Incorrect token entered. try again... {driver_obj.driver_token} != {payload.driver_token}")
        #         raise HTTPException(status_code=status.HTTP_409_CONFLICT,
        #                             detail = "Incorrect token entered. try again...") 
        elif driver_obj.is_registered.lower() == 'registered':
                logger.error(f"Driver has already been {driver_obj.is_registered.lower()}....")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail = "Driver has aready been registered....") 
                
        elif driver_obj.email != payload.email or driver_obj.first_name != payload.first_name and driver_obj.last_name != payload.last_name:
            logger.warning("Information provided does not exist in db")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Data does not exists in db. Check with admin.")
        # 
        elif liscense_exists:
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
