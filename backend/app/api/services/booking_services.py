from fastapi import HTTPException, status, Depends
from app.db.database import get_db
from ..core import deps
from app.models import *
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *
from app.schemas.booking import BookingResponse
from .helper_service import success_resp, success_list_resp
from .service_context import ServiceContext
from .email_services import drivers, tenants
from .helper_service import (
    user_table,
    tenant_table,
    tenant_profile,
    tenant_stats,
    driver_table,
    booking_table,
    tenant_setting_table,
    vehicle_config_table,
    vehicle_category_table,
    vehicle_table
)

from app.models import tenant_setting
db_exceptions = db_error_handler.DBErrorHandler

class BookingService(ServiceContext):
    def __init__(self, db, current_user):
        
        super().__init__(db, current_user)
            
    db_exceptions = db_error_handler.DBErrorHandler
            
    role_to_booking_field  = {
        "driver": booking.Bookings.driver_id,
        "rider": booking.Bookings.rider_id,
        "tenant": booking.Bookings.tenant_id,
        }
    
    async def book_ride(self, payload):
        """Rider books a ride"""
        try:
            price_estimate = await self._price_quote(payload)
            book_ride_info = payload.model_dump()
            vehicle = self.db.query(vehicle_table).filter_by(id=payload.vehicle_id).first()
            if not vehicle:
                raise HTTPException(status_code=404, detail="vehicle not found")

            new_ride = booking.Bookings(rider_id = self.current_user.id,tenant_id = self.current_user.tenant_id,
                                        estimated_price = price_estimate,driver_id = vehicle.driver_id,**book_ride_info)

        
            if not self.db.query(tenant.Tenants).filter(tenant.Tenants.id == self.current_user.tenant_id).first(): 
                raise HTTPException(status_code=404, detail="tenant not found")
        
            
            if not payload.city:
                logger.warning(f"City was not entered for rider {self.current_user.id}")
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail= "City was not entered..")

            #check for overlaps
            self._bookings_overlap( payload)            

            self.db.add(new_ride)
        
            self.db.commit()
            self.db.refresh(new_ride)
            if vehicle.driver_id:
                driver_ = await self._get_driver_fullname(driver_id = new_ride.driver_id)
                driver_full_name = driver_.full_name
                driver_email = driver_.email
                ##email
                # tenants.TenantEmailServices(to_email=self.tenant_email, from_email=self.tenant_email).new_ride(booking)
                drivers.DriverEmailServices(to_email=driver_email, from_email=self.tenant_email).new_ride(booking_obj=new_ride, assigned=False)
            else:
                driver_full_name = "No driver assigned"
            logger.info(f"A new ride has been set for {self.current_user.full_name}")
            
            return success_resp(msg="Booking Successfull", data= {"driver_name": driver_full_name,"customer_name": self.full_name,"vehicle": f"{vehicle.make} {vehicle.model} {vehicle.year}",**new_ride.__dict__})
        
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
    # async def get_booked_rides(self):
    #     try:
    #         user = self.current_user.role
    #         rows = self.role_to_booking_field.get(user.lower())

    #         if not rows:
    #             raise ValueError("Role not in settings")
            
    #         logger.info("All bookings..")
    #         booked_rides = self.db.query(booking.Bookings).filter(rows == self.current_user.id).all()

    #         if not booked_rides:
    #             raise HTTPException(status_code=404, detail = "There are no scheduled rides available")
            
    #         # driver_full_name = await _get_driver_fullname(driver_id = booked_rides.driver_id, db=db)
    #         # return booked_rides

    #         result = []
    #         for ride in booked_rides:
    #             # driver_full_name = None
    #             if ride.driver_id:
    #                 driver_full_name = await self._get_driver_fullname(driver_id=ride.driver_id)
    #                 logger.info(f"{driver_full_name} is the driver")
    #             # logger.info(f"{driver_full_name} is the driver")
                
    #             # logger.info(f"{driver_full_name} is the driver")

    #             ride_dict = ride.__dict__.copy()
    #             ride_dict["driver_fullname"] = driver_full_name
    #             result.append(ride_dict)
    #             # return {"driver_fullname": driver_full_name,
    #                     # **booked_rides.__dict__}
    #         # logger.info(f"{driver_full_name} is the driver")

    #         logger.debug(f"result: {result}")        
    #         return success_resp(msg="Bookings retrieved successfully", data=result)
                  
    #     except db_exceptions.COMMON_DB_ERRORS as e:
    #         db_exceptions.handle(e, self.db)      
            
    async def get_bookings_by(self,booking_id = None ,booking_status: str = None, rider_name: str = None):
        try:
            ####A booking should always have a vehicle_id but booking will not always hav ea driver
            logger.debug(f"I am in here for {booking_status} for {self.role}")
            if booking_status:              
               
                if self.role.lower() == 'tenant':
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                        from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                        where b.tenant_id = :tenant_id or b.booking_status = :booking_status"""
                    
                    booking_query = self.db.execute(text(stmt), {"booking_status":booking_status.lower(), "tenant_id":self.tenant_id})
                        
                elif self.role.lower() == 'driver':
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                        from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id join drivers d on d.id = b.driver_id
                        where b.tenant_id = :tenant_id and b.booking_status = :booking_status and b.driver_id = :driver_id"""
                    booking_query = self.db.execute(text(stmt), {"booking_status":booking_status.lower(), "tenant_id":self.tenant_id, "driver_id":self.driver_id})
                    
                    
                elif self.role.lower() == 'rider':
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                        from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                        where b.tenant_id = :tenant_id and b.booking_status = :booking_status and b.rider_id = :rider_id"""
                    booking_query = self.db.execute(text(stmt), {"booking_status":booking_status.lower(), "tenant_id":self.tenant_id, "rider_id":self.rider_id})
                        
                det = f"There are no {booking_status} bookings right now...."
                msg = f"{booking_status.capitalize()} bookings retrieved successfully"
                meta = {"status": booking_status}
            elif booking_id:
        
                if self.role.lower() == 'tenant':
                    stmt = """select b.* ,  CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                        from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                        where b.tenant_id = :tenant_id and b.id = :booking_id"""
                    
                    booking_query = self.db.execute(text(stmt), {"booking_id":booking_id, "tenant_id":self.tenant_id})
                        
                elif self.role.lower() == 'driver':
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                        from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id join drivers d on d.id = b.driver_id
                        where b.tenant_id = :tenant_id and b.id = :booking_id and b.driver_id = :driver_id"""
                    booking_query = self.db.execute(text(stmt), {"booking_id":booking_id, "tenant_id":self.tenant_id, "driver_id":self.driver_id})
                    
                    
                elif self.role.lower() == 'rider':
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                        from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                        where b.tenant_id = :tenant_id and b.id = :booking_id and b.rider_id = :rider_id"""
                # stmt = "select from drivers"
                    logger.debug(self.tenant_id)
                    booking_query = self.db.execute(text(stmt), {"booking_id":booking_id, "tenant_id":self.tenant_id, "rider_id":self.rider_id})
                det = f"There is no bokings with id {booking_id} ...."
                msg = f"Retrieved booking succcessfully"
                meta = None
                
                
            ###For all bookings
            else: 
                if self.role.lower() == "tenant":
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name 
                            from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                            where b.tenant_id = :tenant_id"""
                    booking_query = self.db.execute(text(stmt), {"tenant_id":self.tenant_id})  
                elif self.role.lower() == "rider":
                    stmt = """select b.* ,  CONCAT(v.make,' ',v.model,' ',v.year) as vehicle , CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name 
                            from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                            where b.tenant_id = :tenant_id and b.rider_id = :rider_id"""
                    booking_query = self.db.execute(text(stmt), {"tenant_id":self.tenant_id ,"rider_id": self.rider_id})
                elif self.role.lower() == "driver":
                    stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name 
                            from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                            where b.tenant_id = :tenant_id and b.driver_id = :driver_id"""
                    booking_query = self.db.execute(text(stmt), {"tenant_id":self.tenant_id ,"driver_id": self.driver_id})
                det = f"There are no bookings...."
                msg = f"Retrieved booking succcessfully"
                meta = None     

                    # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You do not meet role requirement to access all bookings") 
                
            booking_obj:object = booking_query.all()
            
            if not booking_obj:
                return success_resp(meta={"status" :404},
                                    data=booking_obj, msg=det)
                    
            return success_resp(data=booking_obj, msg=msg, meta=meta)
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            
    async def _get_driver_fullname(self, driver_id):
        

        driver = self.db.query(driver_table).filter(driver_table.id == driver_id).first()
        if not driver:
            logger.debug("Driver not in db")
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not in db")
        logger.info(f"{driver.full_name} is the driver for this ride ")
        return driver

    async def _get_vehicle(self, vehicle_id):

        vehicle = self.db.query(vehicle_table).filter(vehicle_table.id == vehicle_id).first()
        if not vehicle:
            logger.info(f"There are no vehicles with {vehicle_id}")
        return f"{vehicle.make} {vehicle.model} {vehicle.year}"
    def _bookings_overlap(self, payload):
     #check for overlaps
        try:
            exists = self.db.query(booking_table).filter(booking_table.vehicle_id == payload.vehicle_id).all()
            """If we implement driver model:
                    cases:
                        if drivers are outsourced or contracted:
                            we will have to check if both the driver and that vehicle are available
                        elif drivers are inhouse:
                            we will check if the vehicle is available and if that 
            """

            logger.info(f"Checking for any booking overlaps")

            if not exists: 
                logger.info(f"There are no overlaps")

                return

            new_start =  payload.pickup_time
            new_end =  payload.dropoff_time

            for booking in exists:
            
                start_time = booking.pickup_time
                end_time = booking.dropoff_time + timedelta(minutes=15)

                if new_start >= new_end:
                    logger.warning(f"strat time {new_start} is greater than end time {new_end}")
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "conflict: start time cannot be higher that end time")

                if (start_time <= new_start <= end_time
                    or start_time <= new_end <= end_time
                        or (payload.pickup_time <= start_time and payload.dropoff_time>= end_time) ):
                    logger.warning(f"Time slot overlap with {booking.id}")
                    
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail = "Time slot overlap with existing booking")
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
        
    async def _price_quote(self, payload):
        try: 
            logger.debug(f"tenant id{self.current_user.tenant_id}")
            settings = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == self.current_user.tenant_id).first()
            vehicle = self.db.query(vehicle_table).filter(vehicle_table.id == payload.vehicle_id).first()
            if not vehicle:
                logger.error(f"Tenant[{self.current_user.tenant_id}] Vehicle was not found at {payload.vehicle_id}")

                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = "Vehicle not found")
            
            vehicle_base_price = self.db.query(vehicle_category_table).filter(vehicle_category_table.id == vehicle.vehicle_category_id).first()
            if not vehicle_base_price:
                logger.error(f"Tenant[{self.current_user.tenant_id}] Vehicle categroy was not found at {vehicle.vehicle_category_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = "Vehicle category not found")
            if not settings:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "Setting for tenants found...")
            #calculate price
            logger.info(f"base_fare = {settings.base_fare}")
            base_fare = settings.base_fare
            per_mile_rate = settings.per_mile_rate
            
            per_minute_rate = settings.per_minute_rate
            vehicle_rate = vehicle_base_price.vehicle_flat_rate
        
            total_quote = base_fare + per_mile_rate + per_minute_rate + vehicle_rate 

            if payload.service_type.lower() == "hourly":
                per_hour_rate = settings.per_hour_rate
                total_quote = total_quote + per_hour_rate

            return round(total_quote, 2)

        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)


def get_booking_service(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return BookingService(db = db, current_user=current_user)
def get_unauthorized_booking_service(db = Depends(get_db)):
    return BookingService(db = db)
